package com.phishing.detection.repository;

import com.phishing.detection.model.Detection;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@TestPropertySource(properties="spring.datasource.url=jdbc:h2:mem:history-test")
class DetectionPersistenceTest {
    @Autowired DetectionRepository repository;

    @Test @Transactional void savesAndReadsDetectionHistory() {
        Detection saved = repository.save(new Detection("PHISHING", "HIGH", 0.91, "Urgent account notice", "{}"));
        assertThat(repository.findById(saved.getId())).isPresent();
        assertThat(repository.countByClassification("PHISHING")).isEqualTo(1);
    }
}
