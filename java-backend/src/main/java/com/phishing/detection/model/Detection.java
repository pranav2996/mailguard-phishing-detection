package com.phishing.detection.model;
import jakarta.persistence.*;
import java.time.Instant;
@Entity @Table(name="detections")
public class Detection {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 private Instant createdAt=Instant.now();
 private String classification; private String riskLevel; private Double confidence;
 @Column(length=1000) private String preview;
 @Lob private String resultJson;
 protected Detection() {}
 public Detection(String classification,String riskLevel,Double confidence,String preview,String resultJson){this.classification=classification;this.riskLevel=riskLevel;this.confidence=confidence;this.preview=preview;this.resultJson=resultJson;}
 public Long getId(){return id;} public Instant getCreatedAt(){return createdAt;} public String getClassification(){return classification;} public String getRiskLevel(){return riskLevel;} public Double getConfidence(){return confidence;} public String getPreview(){return preview;} public String getResultJson(){return resultJson;}
}
