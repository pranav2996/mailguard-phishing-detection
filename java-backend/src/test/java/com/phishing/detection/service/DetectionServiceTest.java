package com.phishing.detection.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.phishing.detection.dto.AnalyzeRequest;
import com.phishing.detection.model.Detection;
import com.phishing.detection.repository.DetectionRepository;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestTemplate;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicReference;
import static org.assertj.core.api.Assertions.assertThat;

class DetectionServiceTest {
    @Test void mapsPythonResponseAndStoresDetection() throws Exception {
        ObjectMapper mapper=new ObjectMapper();
        JsonNode pythonResult=mapper.readTree("{\"classification\":\"PHISHING\",\"confidence\":0.91,\"riskLevel\":\"HIGH\",\"keywords\":{},\"urls\":[],\"reasons\":[\"Model signal\"],\"features\":{}}");
        class StubRestTemplate extends RestTemplate {
            String target; Object request;
            @Override public <T> T postForObject(String url,Object body,Class<T> responseType,Object... uriVariables) {
                target=url; request=body; return responseType.cast(pythonResult);
            }
        }
        var http=new StubRestTemplate();
        AtomicReference<Detection> saved=new AtomicReference<>();
        DetectionRepository repository=(DetectionRepository)Proxy.newProxyInstance(DetectionRepository.class.getClassLoader(),new Class<?>[]{DetectionRepository.class},(proxy,method,args)->{
            if(method.getName().equals("save")){saved.set((Detection)args[0]);return args[0];}
            throw new UnsupportedOperationException(method.getName());
        });
        DetectionService service=new DetectionService(http,repository,mapper);
        Field url=DetectionService.class.getDeclaredField("mlUrl");url.setAccessible(true);url.set(service,"http://127.0.0.1:5000");

        JsonNode result=service.analyze(new AnalyzeRequest("Urgent account notice"));

        assertThat(result.path("classification").asText()).isEqualTo("PHISHING");
        assertThat(result.path("riskLevel").asText()).isEqualTo("HIGH");
        assertThat(http.target).isEqualTo("http://127.0.0.1:5000/predict");
        assertThat(saved.get().getClassification()).isEqualTo("PHISHING");
        assertThat(saved.get().getPreview()).isEqualTo("Urgent account notice");
    }
}
