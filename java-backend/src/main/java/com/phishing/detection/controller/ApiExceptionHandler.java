package com.phishing.detection.controller;
import java.util.Map;
import org.springframework.http.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.HttpClientErrorException;
@RestControllerAdvice
public class ApiExceptionHandler {
 @ExceptionHandler(MethodArgumentNotValidException.class) ResponseEntity<?> invalid(MethodArgumentNotValidException ex){return ResponseEntity.badRequest().body(Map.of("error","Email content is required and must be 50,000 characters or fewer."));}
 @ExceptionHandler(IllegalStateException.class) ResponseEntity<?> unavailable(IllegalStateException ex){return ResponseEntity.status(503).body(Map.of("error",ex.getMessage()));}
 @ExceptionHandler(Exception.class) ResponseEntity<?> other(Exception ex){return ResponseEntity.status(500).body(Map.of("error","The request could not be completed."));}
}
