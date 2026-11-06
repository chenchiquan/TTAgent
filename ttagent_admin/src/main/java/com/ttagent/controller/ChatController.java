package com.ttagent.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ttagent.dto.ChatRequest;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 对话接口（SSE 流式转发）
 *
 * 链路：前端 ChatPanel → Java /api/chat(SSE) → Python /chat → DeepSeek 流式 → 逐 token 回流
 * 用 JDK HttpClient（Java 21 自带）调 Python，SseEmitter 流式转发给前端。
 */
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private static final String PYTHON_CHAT_URL = "http://localhost:8000/chat";
    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final ObjectMapper mapper = new ObjectMapper();

    @PostMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chat(@RequestBody ChatRequest req) {
        // 不超时（流式对话可能较慢）
        SseEmitter emitter = new SseEmitter(0L);

        executor.execute(() -> {
            try {
                // 序列化请求体（和 Python ChatRequest 对齐）
                String body = mapper.writeValueAsString(req);
                System.out.println("[ChatController] 转发 Python body: " + body);

                // 用 JDK HttpClient POST 调 Python /chat
                HttpClient client = HttpClient.newHttpClient();
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(PYTHON_CHAT_URL))
                        .header("Content-Type", "application/json; charset=utf-8")
                        .POST(HttpRequest.BodyPublishers.ofString(body, java.nio.charset.StandardCharsets.UTF_8))
                        .build();

                // 流式按行读 Python 的 SSE 响应
                HttpResponse<java.util.stream.Stream<String>> response =
                        client.send(request, HttpResponse.BodyHandlers.ofLines());

                for (String line : response.body().toList()) {
                    if (line.startsWith("data:")) {
                        String data = line.substring(5).trim();
                        if ("[DONE]".equals(data)) {
                            break;
                        }
                        // 转发给前端
                        emitter.send(SseEmitter.event().data(data));
                    }
                }
                emitter.complete();
            } catch (Exception e) {
                try {
                    emitter.send(SseEmitter.event().data("[ERROR] " + e.getMessage()));
                } catch (Exception ignored) {
                }
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}
