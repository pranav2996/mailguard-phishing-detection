package com.phishing.detection.dto;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
public record AnalyzeRequest(@NotBlank @Size(max=50000) String emailText) {}
