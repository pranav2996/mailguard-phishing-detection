package com.phishing.detection.controller;

import com.phishing.detection.service.DetectionService;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.client.RestTemplate;
import com.phishing.detection.service.DetectionService;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DetectionControllerTest {
    private final MockMvc mvc = MockMvcBuilders
            .standaloneSetup(new DetectionController(new DetectionService(new RestTemplate())))
            .setControllerAdvice(new ApiExceptionHandler())
            .build();

    @Test void rejectsBlankEmail() throws Exception {
        mvc.perform(post("/api/analyze").contentType(MediaType.APPLICATION_JSON).content("{\"emailText\":\"  \"}"))
                .andExpect(status().isBadRequest());
    }

    @Test void rejectsOversizedEmail() throws Exception {
        String input = "x".repeat(50001);
        mvc.perform(post("/api/analyze").contentType(MediaType.APPLICATION_JSON).content("{\"emailText\":\""+input+"\"}"))
                .andExpect(status().isBadRequest());
    }
}
