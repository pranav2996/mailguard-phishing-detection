package com.phishing.detection.repository;
import com.phishing.detection.model.Detection;
import org.springframework.data.jpa.repository.JpaRepository;
public interface DetectionRepository extends JpaRepository<Detection,Long> { long countByClassification(String classification); }
