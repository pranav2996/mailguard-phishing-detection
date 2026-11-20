package com.phishing.detection.controller;

import com.phishing.detection.service.DetectionService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(DetectionController.class)
class DetectionControllerTest {
    @Autowired MockMvc mvc;
    @MockBean DetectionService service;

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
