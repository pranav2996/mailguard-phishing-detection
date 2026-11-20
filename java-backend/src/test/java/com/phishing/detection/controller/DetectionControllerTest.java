package com.phishing.detection.controller;

import com.phishing.detection.service.DetectionService;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.core.annotation.AnnotatedElementUtils;
import java.util.Arrays;
import java.util.Objects;
import org.springframework.web.client.RestTemplate;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.assertj.core.api.Assertions.assertThat;

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

    @Test void historyAndHistoryBasedStatsRoutesDoNotExist() {
        var mappedPaths = Arrays.stream(DetectionController.class.getDeclaredMethods())
                .map(method -> AnnotatedElementUtils.findMergedAnnotation(method, RequestMapping.class))
                .filter(Objects::nonNull)
                .flatMap(mapping -> Arrays.stream(mapping.path()))
                .toList();

        assertThat(mappedPaths).noneMatch(path -> path.contains("history") || path.contains("stats"));
    }
}
