package com.phishing.detection.controller;
import com.fasterxml.jackson.databind.JsonNode;
import com.phishing.detection.dto.AnalyzeRequest;
import com.phishing.detection.service.DetectionService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api")
public class DetectionController {
 private final DetectionService service;
 public DetectionController(DetectionService service){this.service=service;}
 @PostMapping("/analyze") public JsonNode analyze(@Valid @RequestBody AnalyzeRequest request){return service.analyze(request);}
 @GetMapping("/metrics") public JsonNode metrics(){return service.metrics();}
 @GetMapping("/health") public Map<String,Object> health(){return Map.of("status","ok","ml",service.mlHealth());}
}
