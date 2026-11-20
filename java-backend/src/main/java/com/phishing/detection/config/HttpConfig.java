package com.phishing.detection.config;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
@Configuration
public class HttpConfig {
 @Bean RestTemplate restTemplate(RestTemplateBuilder builder, @Value("${ml.service.timeout-ms:5000}") long timeout) { return builder.setConnectTimeout(Duration.ofMillis(timeout)).setReadTimeout(Duration.ofMillis(timeout)).build(); }
 @Bean WebMvcConfigurer cors(@Value("${app.cors.origins}") String origins) { return new WebMvcConfigurer() { public void addCorsMappings(CorsRegistry registry) { registry.addMapping("/api/**").allowedOrigins(origins.split(",")).allowedMethods("GET","POST","OPTIONS"); } }; }
}
