# AI vs. AI: Using Generative Models to Fool Neural Networks

## 📌 Summary

Adversarial attacks represent a critical vulnerability in modern machine learning (ML) systems. This project investigates how generative AI can be used to create subtle, human-imperceptible perturbations that cause deep learning models to make incorrect predictions. We compare traditional attacks like FGSM with generative approaches using models such as Stable Diffusion and StyleGAN2. The experiments are conducted on image classification and object detection tasks using ResNet and YOLOv3 respectively.

---

## 🎯 Objective

To design adversarial attacks using Generative AI that:

- Subtly manipulate input images.
- Preserve visual realism to the human eye.
- Induce misclassifications in deep learning models.
- Compare traditional (FGSM) vs. generative adversarial methods.

---

## 🧪 Methodology

### 1. Model Training & Baseline Evaluation
- Train **ResNet** on CIFAR‑10/MNIST.
- Fine-tune **YOLOv3** on an object detection dataset.
- Evaluate standard accuracy on clean data.

### 2. FGSM-Based Baseline Attack
- Apply FGSM with 50% random chance, using perturbation strengths up to ε = 0.3.
- Record accuracy, confidence, and misclassification rates.

### 3. Generative AI–Driven Adversarial Inputs
- Use pretrained **Stable Diffusion** / **StyleGAN2** (via Hugging Face Diffusers).
- Generate realistic, imperceptible image modifications.

### 4. Model Inference & Evaluation
- Compare model behavior on clean, FGSM-altered, and GenAI-altered inputs.
- Capture metrics:
  - Accuracy Drop
  - Confidence Shifts
  - Misclassification Rate

### 5. Visualization
- Display original vs FGSM vs GenAI images.
- Plot classification confidence and behavior changes.

---

## 🛠️ Tools & Technologies

| Category         | Tools/Frameworks                     |
|------------------|--------------------------------------|
| Language         | Python                               |
| Deep Learning    | PyTorch, Torchvision                 |
| Classification   | ResNet (Transfer Learning)           |
| Detection        | YOLOv3                               |
| Attacks          | FGSM (via Foolbox), Generative AI    |
| Generative Models| Stable Diffusion, StyleGAN2          |
| Libraries        | NumPy, OpenCV, Matplotlib            |

---

## 📚 Theoretical Framework

- **FGSM / PGD**: Gradient-based attacks for baseline robustness evaluation.
- **Generative Perturbations**: Latent space edits that maintain realism.
- **Metrics**: Adversarial Accuracy, Attack Success Rate (ASR), Confidence Shift.
- **Attack Modes**: White-box & Black-box scenarios.

---

## 📈 Expected Outcomes

- ✅ **Visual Stealth**: GenAI-modified images remain human-imperceptible.
- ❌ **Performance Degradation**: Higher misclassification rates expected on GenAI inputs.
- 📊 **Comparative Insights**: FGSM vs GenAI performance, robustness metrics, and stealth analysis.

---

## 🔚 Conclusion

This project demonstrates that generative adversarial inputs can be more deceptive and damaging than traditional attacks like FGSM. By combining rigorous evaluation techniques with modern generative models, we uncover serious robustness issues in deep learning models and stress the importance of adversarial defenses in real-world applications.

---

## 📎 References

- Goodfellow et al., "Explaining and Harnessing Adversarial Examples" (FGSM)
- Carlini & Wagner, "Towards Evaluating the Robustness of Neural Networks"
- Athalye et al., "Synthesizing Robust Adversarial Examples"
- Diffusers: https://huggingface.co/docs/diffusers/

---

## 🚀 Run This Project

> Coming soon: setup instructions, datasets, and scripts for replication.

Stay tuned! ⭐
