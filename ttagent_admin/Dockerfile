# ===== 构建阶段：Maven 编译打包 =====
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
# 先拷 pom.xml，单独装依赖，利用 Docker 层缓存（改代码不重下依赖）
COPY pom.xml .
RUN mvn dependency:go-offline -B
# 拷源码并打包（跳过测试，CI 里再测）
COPY src ./src
RUN mvn clean package -DskipTests -B

# ===== 运行阶段：JRE 跑 jar，镜像小 =====
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
