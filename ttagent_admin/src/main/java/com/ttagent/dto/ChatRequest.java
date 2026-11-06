package com.ttagent.dto;

import lombok.Data;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 对话请求 DTO（前端 → Java → Python）
 */
@Data
public class ChatRequest {
    private String message;
    private List<Map<String, String>> history = new ArrayList<>();  // 默认空列表，避免 null
}
