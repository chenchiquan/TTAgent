package com.ttagent.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ttagent.dto.ChatRequest;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
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

    // Python /chat 地址：容器内用容器名 ai-service，本地开发用 localhost，走环境变量注入
    @Value("${python.chat.url:http://localhost:8000/chat}")
    private String pythonChatUrl;
    // 强制 HTTP/1.1：uvicorn 默认不支持 h2c 升级，HTTP/2 协商会触发 "Unsupported upgrade request"，
    // 导致请求体 body 丢失 → FastAPI 报 422 Field required。
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();
    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final ObjectMapper mapper = new ObjectMapper();

    @PostMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chat(@RequestBody ChatRequest req, HttpServletRequest httpRequest) {
        // 从 JWT 拦截器注入的 userId（阶段1用户登录，为记忆体系铺路）
        req.setUserId((Long) httpRequest.getAttribute("userId"));

        // 不超时（流式对话可能较慢）
        SseEmitter emitter = new SseEmitter(0L);

        executor.execute(() -> {
            try {
                // 序列化请求体（和 Python ChatRequest 对齐）
                String body = mapper.writeValueAsString(req);
                System.out.println("[ChatController] 转发 Python body: " + body);

                // 用 JDK HttpClient POST 调 Python /chat
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(pythonChatUrl))
                        .header("Content-Type", "application/json; charset=utf-8")
                        .POST(HttpRequest.BodyPublishers.ofString(body, java.nio.charset.StandardCharsets.UTF_8))
                        .build();

                // 流式按行读 Python 的 SSE 响应
                HttpResponse<java.util.stream.Stream<String>> response =
                        HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofLines());

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
