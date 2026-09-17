# Test CV — covers edge cases:
# - omitted section (PROJECTS disabled)
# - multiple links in META
# - extras in META (custom contact bar item)
# - link embedded mid-bullet
# - special characters in text (&, <, >)
# - custom section (CERTIFICATIONS)
# - long content to test multi-page flow

---

## META
name: Jane A. O'Brien
profession: Senior Software Engineer
email: jane.obrien@example.com
phone: +1 (555) 867-5309
extras:
  - San Francisco, CA
links:
  - [LinkedIn](https://linkedin.com/in/janeobrien)
  - [GitHub](https://github.com/janeobrien)
  - [Portfolio](https://janeobrien.dev)

---

## SUMMARY
enabled: true
---
Senior Software Engineer with 8+ years of experience building scalable distributed systems. Passionate about clean architecture, developer tooling, and mentoring. Proven track record delivering high-impact features at companies ranging from early-stage startups to Fortune 500 enterprises. Comfortable working across the full stack with a focus on backend systems & cloud infrastructure.

---

## EXPERIENCE
enabled: true
---

### Acme Corp
role: Senior Software Engineer
date: Mar 2021 - Present
bullets:
  - Led migration of monolithic Rails app to microservices on AWS, reducing p99 latency by 40%.
  - Designed & implemented a real-time event pipeline using Kafka & Flink processing 2M+ events/day.
  - Mentored 4 junior engineers; introduced structured code review practices across the team.
  - Collaborated with Product & Design to ship [Acme Dashboard v2](https://acme.example.com/dashboard), increasing DAU by 22%.

### Bright Systems Ltd
role: Software Engineer
date: Jun 2018 - Feb 2021
bullets:
  - Built internal CI/CD tooling using Jenkins, Docker, and Kubernetes cutting deploy time from 45 min to 8 min.
  - Owned the payments integration with Stripe & PayPal; handled PCI-DSS compliance requirements.
  - Contributed to open-source ORM library [bright-orm](https://github.com/brightsystems/bright-orm).

### Startup XYZ
role: Junior Developer
date: Jan 2016 - May 2018
bullets:
  - Developed REST APIs in Node.js/Express serving 50k+ daily active users.
  - Implemented OAuth2 login flow supporting Google, GitHub, and Facebook providers.
  - Wrote unit & integration tests achieving 85% code coverage using Jest & Supertest.

---

## EDUCATION
enabled: true
---

### University of Dublin
degree: Bachelor of Science
field: Computer Science
date: 2012 - 2016
bullets:
  - First Class Honours — GPA 3.9/4.0
  - Thesis: "Optimising Graph Traversal Algorithms for Sparse Networks"
  - Relevant modules: Algorithms & Data Structures, Operating Systems, Distributed Systems, Compilers

---

## PROJECTS
enabled: false
---

### Hidden Project
bullets:
  - This section is disabled and should NOT appear in output.

---

## CERTIFICATIONS
enabled: true
---

### AWS Certified Solutions Architect
org: Amazon Web Services
date: Jan 2023
bullets:
  - Associate level — [Verify credential](https://aws.amazon.com/verification)

### Certified Kubernetes Administrator (CKA)
org: Cloud Native Computing Foundation
date: Aug 2022
bullets:
  - Passed with score 89%. [Certificate](https://cncf.io/certification/cka)

---

## SKILLS
enabled: true
---
Python, Go, Ruby, JavaScript, TypeScript, PostgreSQL, Redis, Kafka, Kubernetes, Docker, AWS, Terraform, Git, Linux

---

## HONORS & AWARDS
enabled: true
---

### Engineer of the Year
org: Acme Corp
date: Dec 2022
bullets:
  - Recognised for outstanding contributions to platform reliability & team culture.

### Hackathon Winner — Best Use of AI
org: TechFest Dublin
date: Oct 2021
bullets:
  - Built a real-time sign language interpreter using MediaPipe & TensorFlow.js. [Demo](https://techfest.example.com/2021/winner)
