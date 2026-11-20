package com.phishing.detection.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.phishing.detection.dto.AnalyzeRequest;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Service
public class DetectionService {
    private final RestTemplate http;

    @Value("${ml.service.url}")
    private String mlUrl;

    @Value("${ml.service.token:}")
    private String mlToken;

    public DetectionService(RestTemplate http) {
        this.http = http;
    }

    public JsonNode analyze(AnalyzeRequest request) {
        try {
            Map<String, String> body = Map.of("emailText", request.emailText());
            JsonNode result = http.postForObject(mlUrl + "/predict", request(body), JsonNode.class);
            if (result == null) {
                throw new IllegalStateException("ML service returned an empty response.");
            }
            return result;
        } catch (RestClientException ex) {
            throw new IllegalStateException("ML service is unavailable. Start the Python service and try again.", ex);
        }
    }

    public JsonNode metrics() {
        try {
            return http.exchange(mlUrl + "/metrics", HttpMethod.GET, request(null), JsonNode.class).getBody();
        } catch (Exception ex) {
            throw new IllegalStateException("Model metrics are unavailable. Train the Python model first.", ex);
        }
    }

    public Map<String, Object> mlHealth() {
        try {
            return http.exchange(mlUrl + "/health", HttpMethod.GET, request(null),
                    new ParameterizedTypeReference<Map<String, Object>>() {}).getBody();
        } catch (Exception ex) {
            return Map.of("status", "unavailable");
        }
    }

    private HttpEntity<Object> request(Object body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (mlToken != null && !mlToken.isBlank()) {
            headers.set("X-Mailguard-Token", mlToken);
        }
        return new HttpEntity<>(body, headers);
    }
}
