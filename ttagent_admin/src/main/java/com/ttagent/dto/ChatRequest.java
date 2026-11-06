package com.ttagent.dto;

import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * 对话请求 DTO（前端 → Java → Python）
 */
@Data
public class ChatRequest {
    private String message;
    private List<Map<String, String>> history;  // [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]
}
