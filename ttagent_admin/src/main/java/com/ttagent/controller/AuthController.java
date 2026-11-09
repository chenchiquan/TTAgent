package com.ttagent.controller;

import com.ttagent.dto.LoginDTO;
import com.ttagent.entity.User;
import com.ttagent.service.UserService;
import com.ttagent.util.JwtUtil;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 认证接口
 * POST /api/auth/register  注册（用户名+密码，BCrypt 加密）
 * POST /api/auth/login     登录，返回 JWT token + userId
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;
    @Autowired
    private JwtUtil jwtUtil;
    @Autowired
    private PasswordEncoder passwordEncoder;

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody @Valid LoginDTO dto) {
        boolean exists = userService.lambdaQuery()
                .eq(User::getUsername, dto.getUsername())
                .exists();
        if (exists) {
            throw new RuntimeException("用户名已存在");
        }
        User u = new User();
        u.setUsername(dto.getUsername());
        u.setPassword(passwordEncoder.encode(dto.getPassword()));
        userService.save(u);
        return Map.of("msg", "注册成功");
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody @Valid LoginDTO dto) {
        User u = userService.lambdaQuery()
                .eq(User::getUsername, dto.getUsername())
                .one();
        if (u == null || !passwordEncoder.matches(dto.getPassword(), u.getPassword())) {
            throw new RuntimeException("用户名或密码错误");
        }
        String token = jwtUtil.generate(u.getId(), u.getUsername());
        return Map.of(
                "token", token,
                "userId", u.getId(),
                "username", u.getUsername()
        );
    }
}
