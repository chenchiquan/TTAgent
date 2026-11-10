"""Memory Manager：候选记忆比对 + 更新决策 + 写库

接收 Extractor 的候选记忆列表，逐条：
1. validate_candidate 校验合法性（JSON三层保障之第三层）
2. 按 memory_action + 现有记忆比对，决定 create/reinforce/update/supersede/reject
3. confidence 由公式计算，不纯靠 LLM 返回值

核心规则（对应需求第四节）：
- 新Key → create
- 同Key同Value → reinforce(evidence_count+1, confidence上调)
- 同Key不同Value + explicit → 旧superseded, 新create
- 同Key不同Value + inferred → 不覆盖, 保留双方等更多证据
- reject → 旧rejected
- temporary → 不写入长期记忆
"""
import re

from memory.models import PlayerMemoryKv, STATUS_ACTIVE
from memory import store

# ===== 校验常量（JSON第三层保障）=====
ALLOWED_CATEGORIES = {"weapon", "map", "ammo", "combat"}
KEY_PATTERN = re.compile(r"^(weapon|map|ammo|combat)\.[a-z_]+$")
ALLOWED_EXPRESSION = {"explicit", "repeated_behavior", "inferred", "temporary"}
ALLOWED_ACTION = {"create", "reinforce", "update", "contradict", "reject"}

# ===== confidence 计算常量 =====
BASE_CONFIDENCE = {
    "explicit": 0.6,
    "repeated_behavior": 0.5,
    "inferred": 0.3,
    "temporary": 0.1,
}
MAX_CONFIDENCE = 0.95
EVIDENCE_STEP = 0.1  # 每次强化上调 0.1


def validate_candidate(candidate: dict) -> str | None:
    """校验候选记忆合法性，返回错误描述或 None(合法)

    JSON三层保障之第三层：入库前业务校验，拦住 LLM 返回的非法数据
    """
    cat = candidate.get("category")
    if cat not in ALLOWED_CATEGORIES:
        return f"非法 category: {cat}，允许 {ALLOWED_CATEGORIES}"

    key = candidate.get("memory_key", "")
    if not KEY_PATTERN.match(key):
        return f"memory_key 不符合命名规范: {key}"

    val = candidate.get("memory_value")
    if not isinstance(val, dict) or not val:
        return f"memory_value 必须是非空 dict，得到 {type(val).__name__}"
    if "preference" not in val or not val["preference"]:
        return "memory_value 缺少 preference 字段或为空"

    expr = candidate.get("expression_type", "explicit")
    if expr not in ALLOWED_EXPRESSION:
        return f"非法 expression_type: {expr}"

    action = candidate.get("memory_action", "create")
    if action not in ALLOWED_ACTION:
        return f"非法 memory_action: {action}"

    conf = candidate.get("confidence", 0)
    try:
        if not (0 <= float(conf) <= 1):
            return f"confidence 越界: {conf}"
    except (TypeError, ValueError):
        return f"confidence 非数值: {conf}"

    src = candidate.get("source_message_ids")
    if not isinstance(src, list) or not src:
        return "source_message_ids 必须是非空数组"

    return None  # 合法


def calc_confidence(expression_type: str, evidence_count: int, llm_confidence: float = 0) -> float:
    """计算最终 confidence

    不纯靠 LLM 返回值，由 expression_type base + evidence_count 上调决定
    LLM 返回值仅作参考（取 max 比较，但不让它超过公式上限）
    """
    base = BASE_CONFIDENCE.get(expression_type, 0.3)
    formula = base + (evidence_count - 1) * EVIDENCE_STEP
    # 取公式值和 LLM 值的较大者，但不超过 MAX_CONFIDENCE
    return round(min(MAX_CONFIDENCE, max(formula, llm_confidence)), 2)


def _norm_preference(val) -> str:
    """标准化 preference 用于比对（小写 + 去首尾空格）"""
    return str(val or "").strip().lower()


def process_candidates(user_id: int, candidates: list[dict]) -> dict:
    """处理候选记忆列表，逐条比对+写库

    Args:
        user_id: 用户 id
        candidates: extractor 返回的候选记忆列表
    Returns:
        统计结果 {"total":N, "created":N, "reinforced":N, "updated":N,
                 "rejected":N, "skipped":N, "errors":[...]}
    """
    result = {"total": len(candidates), "created": 0, "reinforced": 0,
              "updated": 0, "rejected": 0, "skipped": 0, "errors": []}

    for i, cand in enumerate(candidates):
        # 1. 校验
        err = validate_candidate(cand)
        if err:
            result["errors"].append(f"候选#{i}: {err}")
            result["skipped"] += 1
            continue

        expr = cand["expression_type"]

        # 2. temporary 临时意图不写入长期记忆
        if expr == "temporary":
            print(f"[manager] 跳过临时意图 user_id={user_id} key={cand['memory_key']}")
            result["skipped"] += 1
            continue

        action = cand["memory_action"]
        key = cand["memory_key"]
        src_ids = cand["source_message_ids"]

        # 3. 查现有 active 记忆
        existing = store.get_active_kv_by_key(user_id, key)

        # 4. 按 action + 现有记忆情况决策
        if action == "reject":
            # 玩家明确否定：把现有记忆标 rejected
            if existing:
                store.reject_kv(existing.id)
                print(f"[manager] reject user_id={user_id} key={key} (kv_id={existing.id})")
                result["rejected"] += 1
            else:
                print(f"[manager] reject 无现有记忆可否定 user_id={user_id} key={key}")
                result["skipped"] += 1
            continue

        if not existing:
            # 无现有记忆 → create（不管 action 是 create/reinforce/update/contradict）
            kv = _build_kv(user_id, cand, version=1)
            kv_id = store.insert_kv(kv)
            print(f"[manager] create user_id={user_id} key={key} (kv_id={kv_id})")
            result["created"] += 1
            continue

        # 有现有记忆，比对 preference 是否相同
        new_pref = _norm_preference(cand["memory_value"]["preference"])
        old_pref = _norm_preference(existing.memory_value.get("preference", ""))

        if new_pref == old_pref:
            # 同 Key 同 Value → reinforce
            new_ev = existing.evidence_count + 1
            new_conf = calc_confidence(expr, new_ev, float(cand.get("confidence", 0)))
            store.reinforce_kv(existing.id, new_conf, src_ids)
            print(f"[manager] reinforce user_id={user_id} key={key} (kv_id={existing.id} ev={new_ev} conf={new_conf})")
            result["reinforced"] += 1
        else:
            # 同 Key 不同 Value
            if expr == "explicit":
                # 明确改偏好：旧 superseded，新 create（version+1）
                new_ver = existing.version + 1
                store.supersede_kv(existing.id)
                kv = _build_kv(user_id, cand, version=new_ver)
                kv_id = store.insert_kv(kv)
                print(f"[manager] update user_id={user_id} key={key} 旧(id={existing.id} v{existing.version})superseded 新(id={kv_id} v{new_ver})")
                result["updated"] += 1
            else:
                # inferred/contradict 推断冲突：不覆盖，保留双方，等更多证据
                print(f"[manager] 冲突不覆盖 user_id={user_id} key={key} 旧pref={old_pref} 新pref={new_pref} expr={expr} (等更多证据)")
                result["skipped"] += 1

    return result


def _build_kv(user_id: int, cand: dict, version: int) -> PlayerMemoryKv:
    """从候选记忆构造 ORM 对象（供 insert）"""
    expr = cand["expression_type"]
    llm_conf = float(cand.get("confidence", 0))
    conf = calc_confidence(expr, evidence_count=1, llm_confidence=llm_conf)

    return PlayerMemoryKv(
        user_id=user_id,
        category=cand["category"],
        memory_key=cand["memory_key"],
        memory_value=cand["memory_value"],  # dict，SQLAlchemy JSON 自动序列化
        confidence=conf,
        evidence_count=1,
        expression_type=expr,
        source_message_ids=cand["source_message_ids"],
        status=STATUS_ACTIVE,
        version=version,
    )
