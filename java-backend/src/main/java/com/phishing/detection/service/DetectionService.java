package com.phishing.detection.service;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.phishing.detection.dto.AnalyzeRequest;
import com.phishing.detection.model.Detection;
import com.phishing.detection.repository.DetectionRepository;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
@Service
public class DetectionService {
 private final RestTemplate http; private final DetectionRepository repository; private final ObjectMapper mapper;
 @Value("${ml.service.url}") private String mlUrl;
 @Value("${ml.service.token:}") private String mlToken;
 public DetectionService(RestTemplate http,DetectionRepository repository,ObjectMapper mapper){this.http=http;this.repository=repository;this.mapper=mapper;}
 public JsonNode analyze(AnalyzeRequest request){
  try {
   Map<String,String> body=Map.of("emailText",request.emailText());
   JsonNode result=http.postForObject(mlUrl+"/predict",request(body),JsonNode.class);
   if(result==null) throw new IllegalStateException("ML service returned an empty response.");
   String classification=result.path("classification").asText("UNKNOWN"), risk=result.path("riskLevel").asText("UNKNOWN");
   Double confidence=result.path("confidence").isNumber()?result.path("confidence").asDouble():null;
   String preview=request.emailText().replaceAll("\\s+"," ").trim(); if(preview.length()>180) preview=preview.substring(0,180)+"…";
   Detection stored=repository.save(new Detection(classification,risk,confidence,preview,mapper.writeValueAsString(result)));
   var response=(com.fasterxml.jackson.databind.node.ObjectNode)result;
   response.put("id",stored.getId()); response.put("createdAt",stored.getCreatedAt().toString());
   return result;
  } catch(RestClientException ex){ throw new IllegalStateException("ML service is unavailable. Start the Python service and try again.",ex); }
    catch(Exception ex){if(ex instanceof IllegalStateException) throw (IllegalStateException)ex; throw new IllegalStateException("Could not process the detection result.",ex);}
 }
 public List<JsonNode> history(){return repository.findAll(org.springframework.data.domain.Sort.by(org.springframework.data.domain.Sort.Direction.DESC,"createdAt")).stream().map(d->{try{var n=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(d.getResultJson());n.put("id",d.getId());n.put("createdAt",d.getCreatedAt().toString());n.put("preview",d.getPreview());return (JsonNode)n;}catch(Exception e){return mapper.createObjectNode().put("id",d.getId()).put("classification",d.getClassification()).put("riskLevel",d.getRiskLevel()).put("createdAt",d.getCreatedAt().toString()).put("preview",d.getPreview());}}).toList();}
 public Map<String,Object> stats(){return Map.of("total",repository.count(),"phishing",repository.countByClassification("PHISHING"),"safe",repository.countByClassification("SAFE"));}
 public JsonNode metrics(){try{return http.exchange(mlUrl+"/metrics",HttpMethod.GET,request(null),JsonNode.class).getBody();}catch(Exception e){throw new IllegalStateException("Model metrics are unavailable. Train the Python model first.",e);}}
 public Map<String,Object> mlHealth(){try{return http.exchange(mlUrl+"/health",HttpMethod.GET,request(null),Map.class).getBody();}catch(Exception e){return Map.of("status","unavailable");}}
 private HttpEntity<Object> request(Object body){HttpHeaders headers=new HttpHeaders();headers.setContentType(MediaType.APPLICATION_JSON);if(mlToken!=null&&!mlToken.isBlank())headers.set("X-Mailguard-Token",mlToken);return new HttpEntity<>(body,headers);}
}
