"""Fixture metadata + text for sample job descriptions.

Seeded into the JobDescription table + ChromaDB when a user picks samples
from the Resume Report JD choice UI. Lives under `app/data/` so the API can
load them without requiring users to upload files.

Expanded to 40 JDs covering: Software Engineering, Frontend, Backend, Full Stack,
AI/ML, Data, Product, Design, DevOps, Cloud, Security, QA, Mobile, Game Dev,
Embedded, Business Analysis, and Project Management.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleJobDescriptionFixture:
    id: str
    role_title: str
    category: str
    summary: str
    filename: str
    parsed_text: str


SAMPLE_JOB_DESCRIPTIONS: list[SampleJobDescriptionFixture] = [
    # ─── Software Engineering ────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="software-engineer",
        role_title="Software Engineer",
        category="Engineering",
        summary="Build product features across a modern TypeScript / Python stack.",
        filename="sample_software_engineer.txt",
        parsed_text="""\
Job Title: Software Engineer
Company: TechFlow Inc. — Series B SaaS startup, 120 employees

About the role
We are hiring a Software Engineer to design, build, and ship reliable product
features for a B2B SaaS platform used by 500+ enterprise customers. You will
work closely with product and design to deliver well-tested services and
polished user experiences.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Design and implement backend APIs and frontend features end-to-end
- Write clean, well-tested TypeScript and Python code
- Participate in code reviews and technical design discussions
- Collaborate with product managers on scoping and trade-offs
- Improve observability, performance, and reliability of production systems
- Triage and resolve production incidents

Required skills
- Strong proficiency in TypeScript or JavaScript (3+ years)
- Experience with React and REST APIs
- Comfortable with Git, SQL, and cloud deployment basics
- Clear written and verbal communication
- Understanding of software design patterns

Nice to have
- Python / FastAPI backend experience
- Docker and CI/CD pipelines
- System design fundamentals
- Experience with GraphQL

Compensation: $120,000 – $160,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="frontend-engineer",
        role_title="Frontend Engineer",
        category="Engineering",
        summary="Craft pixel-perfect, performant React UIs that delight millions of users.",
        filename="sample_frontend_engineer.txt",
        parsed_text="""\
Job Title: Frontend Engineer
Company: Pixel Labs — consumer product startup, 80 employees

About the role
We are building the most beautiful consumer finance app in the market and need
a Frontend Engineer who obsesses over performance, accessibility, and visual
detail. You will own entire feature areas of our React application.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Build reusable React component libraries with TypeScript
- Implement responsive, accessible UIs from Figma designs with pixel precision
- Optimize bundle size, Core Web Vitals, and rendering performance
- Write unit and integration tests (Jest, React Testing Library)
- Collaborate with backend engineers on API contracts
- Champion accessibility standards (WCAG 2.1 AA)

Required skills
- Expert-level React (hooks, context, concurrent features) — 3+ years
- TypeScript proficiency
- Strong CSS skills (Flexbox, Grid, animations)
- Familiarity with build tooling (Vite / Webpack)
- Experience with state management (Zustand, Redux Toolkit, or React Query)

Nice to have
- Framer Motion or GSAP animation experience
- Next.js or SSR/SSG experience
- Design systems and Storybook
- Web performance profiling (Lighthouse, Chrome DevTools)

Compensation: $130,000 – $175,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="backend-engineer",
        role_title="Backend Engineer",
        category="Engineering",
        summary="Design and operate the distributed systems that power our platform at scale.",
        filename="sample_backend_engineer.txt",
        parsed_text="""\
Job Title: Backend Engineer
Company: ScaleOps — infrastructure platform, Series C, 200 employees

About the role
Our backend team owns the API layer, data pipelines, and infrastructure that
serve 10M+ requests per day. We are looking for a Backend Engineer who thinks
deeply about reliability, latency, and data consistency.

Experience Level: Mid-to-senior (3–7 years)

Responsibilities
- Design and implement high-throughput REST and gRPC APIs
- Own database schema design, query optimization, and migrations
- Build async workers, job queues, and event-driven pipelines
- Write rigorous unit, integration, and load tests
- Participate in on-call rotation and incident response
- Mentor junior engineers

Required skills
- Python (FastAPI / Django) or Go — 3+ years
- PostgreSQL or similar relational database (indexing, query plans)
- Redis for caching and pub/sub
- Experience with message brokers (Kafka, RabbitMQ, or SQS)
- Docker and Kubernetes basics

Nice to have
- Distributed systems concepts (CAP theorem, eventual consistency)
- gRPC and Protocol Buffers
- Elasticsearch or OpenSearch
- Infrastructure as Code (Terraform)

Compensation: $140,000 – $185,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="fullstack-engineer",
        role_title="Full Stack Engineer",
        category="Engineering",
        summary="Own features end-to-end — from database schema to polished UI.",
        filename="sample_fullstack_engineer.txt",
        parsed_text="""\
Job Title: Full Stack Engineer
Company: Buildfast — no-code platform startup, Series A, 50 employees

About the role
Small team, big scope. As a Full Stack Engineer, you will own full features
from database to deployment: designing APIs, building React frontends, and
shipping to production every week.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Build React / TypeScript frontends and Python / Node.js backends
- Design PostgreSQL schemas and write efficient queries
- Deploy and monitor services on AWS
- Write comprehensive tests across the stack
- Participate in product roadmap discussions

Required skills
- React and TypeScript (2+ years)
- Python (FastAPI or Flask) or Node.js backend experience
- PostgreSQL and basic SQL query optimisation
- REST API design
- Git workflow and code review

Nice to have
- Next.js for SSR
- AWS (Lambda, RDS, S3, CloudFront)
- CI/CD with GitHub Actions
- Familiarity with Docker

Compensation: $110,000 – $155,000 base + equity
""",
    ),
    # ─── AI / ML Engineering ─────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="ai-engineer",
        role_title="AI Engineer",
        category="AI/ML",
        summary="Productionize LLM-powered features and agentic workflows at scale.",
        filename="sample_ai_engineer.txt",
        parsed_text="""\
Job Title: AI Engineer
Company: Cortex AI — LLM application platform, Series B, 90 employees

About the role
We build AI-powered products on top of foundation models (OpenAI GPT-4,
Anthropic Claude, Google Gemini). We need an AI Engineer who bridges the gap
between research and production: prompt engineering, RAG pipelines, fine-tuning,
and monitoring AI systems in the wild.

Experience Level: Mid-to-senior (2–5 years in software + 1+ year in AI/ML)

Responsibilities
- Design and iterate on prompts, chains, and agentic workflows
- Build RAG systems: chunking, embedding, vector database retrieval
- Evaluate and benchmark model outputs (evals, human raters)
- Monitor latency, token costs, and quality drift in production
- Integrate AI capabilities into product features via clean APIs
- Stay current with the LLM research landscape

Required skills
- Python proficiency and software engineering fundamentals
- Hands-on experience with OpenAI, Anthropic, or Gemini APIs
- LangChain, LlamaIndex, or equivalent orchestration framework
- Vector databases (Pinecone, Chroma, Weaviate, or Qdrant)
- Prompt engineering and few-shot learning techniques

Nice to have
- Fine-tuning (LoRA, QLoRA, full-parameter)
- LLM evaluation frameworks (RAGAS, deepeval)
- MLOps basics (experiment tracking, model versioning)
- Understanding of transformer architecture

Compensation: $150,000 – $210,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="ml-engineer",
        role_title="Machine Learning Engineer",
        category="AI/ML",
        summary="Build and ship ML models from experimentation to reliable production systems.",
        filename="sample_ml_engineer.txt",
        parsed_text="""\
Job Title: Machine Learning Engineer
Company: Predict Labs — ML platform company, Series B, 150 employees

About the role
You will own the full ML lifecycle: collaborating with researchers on models,
building training pipelines, deploying inference endpoints, and monitoring
model performance in production.

Experience Level: Mid-level (3–5 years)

Responsibilities
- Build scalable model training and evaluation pipelines
- Deploy models as low-latency inference APIs (REST / gRPC)
- Implement feature engineering and feature store integration
- Monitor model quality, data drift, and performance SLAs
- Work with data engineers to ensure high-quality training data
- Collaborate with researchers to translate papers into production code

Required skills
- Python (scikit-learn, PyTorch or TensorFlow)
- Experiment tracking (MLflow, Weights & Biases)
- Cloud ML services (AWS SageMaker, GCP Vertex AI, or Azure ML)
- SQL and data manipulation (pandas, Spark basics)
- Software engineering best practices (testing, CI/CD, code review)

Nice to have
- Kubeflow or Airflow for pipeline orchestration
- ONNX / TensorRT model optimization
- Distributed training (PyTorch DDP, FSDP)
- Knowledge of recommendation systems or NLP

Compensation: $140,000 – $195,000 base + equity
""",
    ),
    # ─── Data ─────────────────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="data-scientist",
        role_title="Data Scientist",
        category="Data",
        summary="Turn messy datasets into models and insights that drive product decisions.",
        filename="sample_data_scientist.txt",
        parsed_text="""\
Job Title: Data Scientist
Company: Insight Analytics — B2B analytics SaaS, 180 employees

About the role
Join our analytics team to build predictive models, design experiments, and
communicate insights that shape product strategy and revenue.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Clean, explore, and analyse large, complex datasets
- Build, validate, and iterate on machine learning models
- Partner with engineers to productionise model features
- Present findings clearly to non-technical stakeholders and leadership
- Design A/B tests and interpret results with statistical rigour

Required skills
- Python (pandas, scikit-learn, statsmodels) — 2+ years
- SQL and statistical reasoning (hypothesis testing, regression)
- Experience with experimentation / causal analysis
- Strong data storytelling and visualisation (Matplotlib, Seaborn, Tableau)
- Solid understanding of probability and statistics

Nice to have
- PyTorch or TensorFlow for deep learning
- Feature stores / MLOps basics
- Product analytics tools (Amplitude, Mixpanel, Looker)
- Time-series forecasting

Compensation: $125,000 – $170,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="data-analyst",
        role_title="Data Analyst",
        category="Data",
        summary="Transform raw data into actionable insights that guide business strategy.",
        filename="sample_data_analyst.txt",
        parsed_text="""\
Job Title: Data Analyst
Company: GrowthMetrics — marketing analytics company, 70 employees

About the role
We are looking for a Data Analyst to help our clients understand what is
working in their marketing, product, and operations. You will own dashboards,
ad-hoc analysis, and regular reporting for a portfolio of accounts.

Experience Level: Junior-to-mid (1–4 years)

Responsibilities
- Write SQL queries to pull, clean, and transform data
- Build and maintain dashboards in Tableau, Looker, or Power BI
- Conduct ad-hoc analyses to answer business questions
- Communicate insights and recommendations to stakeholders
- Identify data quality issues and work with engineers to fix them
- Automate recurring reports

Required skills
- Advanced SQL (window functions, CTEs, joins)
- Dashboard tooling (Tableau, Power BI, Looker, or Metabase)
- Excel / Google Sheets for quick analyses
- Clear written communication
- Basic statistics and data interpretation

Nice to have
- Python (pandas) for data transformation
- dbt for data modelling
- Experience with GA4, Segment, or similar event tracking
- Business domain knowledge (marketing, finance, or operations)

Compensation: $75,000 – $110,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="data-engineer",
        role_title="Data Engineer",
        category="Data",
        summary="Build the pipelines and platforms that make data accessible, reliable, and fast.",
        filename="sample_data_engineer.txt",
        parsed_text="""\
Job Title: Data Engineer
Company: DataFlow Systems — data infrastructure startup, Series A, 60 employees

About the role
Our data team builds the backbone of a modern data platform: ingestion,
transformation, storage, and serving. We are looking for a Data Engineer
who loves building reliable pipelines and cares about data quality.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Build and maintain batch and streaming data pipelines
- Implement data models and transformations using dbt
- Manage and optimise data warehouses (Snowflake, BigQuery, or Redshift)
- Ensure data quality with monitoring and automated testing
- Work with analysts and data scientists to understand data needs

Required skills
- SQL and data modelling expertise
- Python for ETL scripting
- Airflow or Prefect for pipeline orchestration
- Cloud data warehouse (Snowflake, BigQuery, or Redshift)
- Basic knowledge of streaming (Kafka or Kinesis)

Nice to have
- Spark for large-scale transformations
- dbt advanced features (macros, packages)
- Terraform for infrastructure
- Real-time streaming architectures

Compensation: $120,000 – $165,000 base + equity
""",
    ),
    # ─── Product & Project Management ──────────────────────────────────────
    SampleJobDescriptionFixture(
        id="product-manager",
        role_title="Product Manager",
        category="Product",
        summary="Own roadmap outcomes — discovery, prioritization, and cross-functional delivery.",
        filename="sample_product_manager.txt",
        parsed_text="""\
Job Title: Product Manager
Company: BuildRight — productivity SaaS, Series B, 200 employees

About the role
We are looking for a Product Manager to own a core product area end-to-end:
discovery, roadmap, delivery, and measurable outcomes.

Experience Level: Mid-level (3–6 years)

Responsibilities
- Define problem statements, success metrics, and OKRs for your area
- Prioritise backlog collaboratively with engineering and design
- Run customer interviews and synthesise insights into requirements
- Write clear PRDs, user stories, and launch plans
- Measure impact post-launch and iterate based on data

Required skills
- Product discovery and prioritisation frameworks (JTBD, impact/effort, RICE)
- Excellent stakeholder communication (eng, design, leadership)
- Comfort with analytics and SQL for product data
- Experience shipping software products with engineering teams
- Strong written and verbal communication

Nice to have
- B2B SaaS domain experience
- A/B testing literacy
- Technical background (CS or engineering degree)
- Experience with enterprise customers

Compensation: $130,000 – $175,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="product-manager-ai",
        role_title="AI Product Manager",
        category="Product",
        summary="Drive the roadmap for AI-powered features used by 1M+ users.",
        filename="sample_ai_product_manager.txt",
        parsed_text="""\
Job Title: AI Product Manager
Company: Luminary AI — consumer AI app, Series C, 300 employees

About the role
As the AI Product Manager, you will own the roadmap for our generative AI
features: prompt UX, AI content quality, feedback loops, and trust-and-safety.
You will work directly with ML engineers and researchers to bring AI capabilities
to life for millions of users.

Experience Level: Senior (5+ years PM experience, 1+ year in AI products)

Responsibilities
- Define and prioritise the AI feature roadmap based on user research and data
- Work closely with ML engineers to set model quality requirements and evals
- Design feedback loops and RLHF data collection strategies
- Balance AI capability with responsible AI principles
- Communicate AI product strategy to leadership and external stakeholders

Required skills
- Track record shipping AI-powered features at scale
- Ability to deeply understand LLM capabilities and limitations
- Strong user research and data analysis skills
- Experience setting model quality metrics and evaluation criteria
- Excellent communication and stakeholder management

Nice to have
- Technical background in ML or data science
- Experience with content moderation or trust-and-safety
- Understanding of model fine-tuning and evaluation pipelines
- B2C consumer product experience at scale

Compensation: $160,000 – $220,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="project-manager",
        role_title="Project Manager",
        category="Management",
        summary="Drive complex technical projects to on-time, on-budget delivery.",
        filename="sample_project_manager.txt",
        parsed_text="""\
Job Title: Project Manager (Technical)
Company: Meridian Consulting — technology consulting, 500 employees

About the role
We need a Project Manager who can own complex technical delivery: coordinating
cross-functional teams, managing risk, tracking milestones, and communicating
progress to executive stakeholders.

Experience Level: Mid-to-senior (4–8 years)

Responsibilities
- Define project scope, milestones, and success criteria
- Build and maintain project plans, resource allocations, and budgets
- Facilitate daily stand-ups, sprint planning, and retrospectives
- Identify and mitigate risks proactively
- Escalate blockers and communicate status to leadership
- Drive continuous improvement in delivery processes

Required skills
- PMP, PRINCE2, or equivalent certification (or in progress)
- Experience managing software engineering projects
- Proficiency with Jira, Asana, or similar tools
- Strong risk management and stakeholder communication
- Agile / Scrum facilitation

Nice to have
- Technical background (engineering or CS)
- SAFe or scaled agile frameworks
- Budget ownership and financial reporting
- Client-facing consulting experience

Compensation: $100,000 – $145,000 base + bonus
""",
    ),
    # ─── Design ────────────────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="ux-designer",
        role_title="UX Designer",
        category="Design",
        summary="Craft research-backed flows and interface systems for a growing product.",
        filename="sample_ux_designer.txt",
        parsed_text="""\
Job Title: UX Designer
Company: Clarity Design Studio — product design agency, 40 employees

About the role
Design clear, accessible product experiences. You will partner with PMs and
engineers from research through high-fidelity UI for a range of B2B clients.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Conduct user research (interviews, usability tests, surveys)
- Create wireframes, user flows, prototypes, and high-fidelity designs
- Collaborate with engineers on implementation fidelity
- Advocate for accessibility and inclusive design principles
- Present work, incorporate critique, and iterate rapidly

Required skills
- Figma proficiency (components, auto layout, variables)
- Interaction design and information architecture
- Portfolio demonstrating shipped product work
- User research methodology
- Strong cross-functional collaboration

Nice to have
- Design systems experience
- Motion design and micro-interaction craft
- Basic HTML/CSS literacy
- Experience with enterprise or B2B products

Compensation: $100,000 – $145,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="ui-designer",
        role_title="UI Designer",
        category="Design",
        summary="Create stunning visual interfaces that balance beauty with clarity.",
        filename="sample_ui_designer.txt",
        parsed_text="""\
Job Title: UI Designer
Company: Spark Creative — digital product agency, 60 employees

About the role
We are looking for a UI Designer who brings exceptional visual craft to digital
products. You will translate UX wireframes into polished, production-ready
high-fidelity designs that inspire.

Experience Level: Mid-level (2–4 years)

Responsibilities
- Create high-fidelity UI designs from wireframes and briefs
- Develop and maintain design systems and component libraries
- Ensure visual consistency across all product surfaces
- Create icon sets, illustrations, and branded UI assets
- Collaborate with UX designers and developers on handoff quality

Required skills
- Figma expertise (variants, auto layout, prototyping)
- Strong visual design fundamentals (typography, colour, spacing)
- Understanding of responsive design and mobile design patterns
- Portfolio showcasing visual design and UI craft
- Attention to detail and visual precision

Nice to have
- Motion design experience (Lottie, Principle, Rive)
- Brand identity and illustration skills
- Basic CSS implementation knowledge
- Dark mode and accessibility design

Compensation: $85,000 – $125,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="product-designer",
        role_title="Product Designer",
        category="Design",
        summary="Own the end-to-end design of product features from discovery to launch.",
        filename="sample_product_designer.txt",
        parsed_text="""\
Job Title: Product Designer
Company: Onyx — B2B fintech startup, Series A, 70 employees

About the role
As a Product Designer, you will be the sole designer for a product area: running
your own user research, creating flows and prototypes, and shipping polished UI
working side-by-side with engineers.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Lead discovery: user interviews, competitive analysis, journey mapping
- Define information architecture, user flows, and interaction models
- Create wireframes, prototypes, and high-fidelity designs in Figma
- Build and maintain the product design system
- QA designs in development to ensure implementation fidelity

Required skills
- Full UX/UI skillset (research → wireframes → visual design)
- Figma mastery
- Strong portfolio of shipped products
- Ability to communicate design decisions with data and rationale
- Experience working directly with engineering teams

Nice to have
- Fintech, banking, or regulated industry experience
- Design systems at scale
- Accessibility expertise
- Data-informed design using analytics

Compensation: $120,000 – $165,000 base + equity
""",
    ),
    # ─── DevOps / Cloud / Infrastructure ──────────────────────────────────
    SampleJobDescriptionFixture(
        id="devops-engineer",
        role_title="DevOps Engineer",
        category="Infrastructure",
        summary="Build CI/CD pipelines and keep our cloud infrastructure reliable and fast.",
        filename="sample_devops_engineer.txt",
        parsed_text="""\
Job Title: DevOps Engineer
Company: CloudBase — SaaS infrastructure company, 130 employees

About the role
We are looking for a DevOps Engineer to own CI/CD, container orchestration, and
monitoring for a high-traffic SaaS platform. You will work closely with
engineering teams to remove deployment friction and improve reliability.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Design and maintain CI/CD pipelines (GitHub Actions, GitLab CI, or CircleCI)
- Manage Kubernetes clusters on AWS (EKS) or GCP (GKE)
- Implement Infrastructure as Code with Terraform
- Set up monitoring, alerting, and logging (Datadog, Prometheus, Grafana)
- Enforce security best practices (IAM, secrets management, network policies)
- Participate in on-call rotation and incident response

Required skills
- Kubernetes (deployment, services, Helm charts)
- Docker and container security
- Terraform or Pulumi for IaC
- AWS or GCP fundamentals (VPC, IAM, compute, storage)
- CI/CD pipelines and GitOps

Nice to have
- Service mesh (Istio, Linkerd)
- ArgoCD or Flux for GitOps
- Vault for secrets management
- Python or Go scripting

Compensation: $130,000 – $175,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="cloud-engineer",
        role_title="Cloud Engineer",
        category="Infrastructure",
        summary="Design and manage multi-cloud architectures for enterprise clients.",
        filename="sample_cloud_engineer.txt",
        parsed_text="""\
Job Title: Cloud Engineer
Company: Nexus Cloud Partners — cloud consulting, 250 employees

About the role
As a Cloud Engineer, you will help enterprise clients migrate to and optimise
their cloud infrastructure across AWS, Azure, and GCP. Projects range from
lift-and-shift migrations to modern serverless architectures.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Architect and implement cloud infrastructure solutions for clients
- Migrate on-premises workloads to cloud platforms
- Optimise cloud costs and performance
- Write Terraform / CloudFormation / Bicep for repeatable deployments
- Implement cloud security best practices and compliance controls
- Provide technical documentation and knowledge transfer to clients

Required skills
- AWS Solutions Architect Associate (or equivalent Azure/GCP certification)
- Terraform for infrastructure as code
- Networking (VPCs, DNS, load balancers, CDN)
- Database services (RDS, DynamoDB, Cloud SQL)
- Linux system administration

Nice to have
- Multi-cloud architecture experience
- Cloud cost optimisation (AWS Cost Explorer, GCP Billing)
- Kubernetes and container platforms
- Security and compliance (SOC2, HIPAA, PCI-DSS)

Compensation: $120,000 – $165,000 base + bonuses
""",
    ),
    SampleJobDescriptionFixture(
        id="site-reliability-engineer",
        role_title="Site Reliability Engineer",
        category="Infrastructure",
        summary="Keep our platform at five-nines availability while engineers ship fast.",
        filename="sample_sre.txt",
        parsed_text="""\
Job Title: Site Reliability Engineer (SRE)
Company: Velocity Systems — fintech platform, Series C, 350 employees

About the role
Our SRE team owns availability, latency, and scalability of a financial
transaction platform processing $5B/year. We embed reliability engineering
into every engineering team via SLOs, error budgets, and chaos engineering.

Experience Level: Senior (5+ years)

Responsibilities
- Define and enforce SLOs, SLIs, and error budgets
- Build and maintain observability stack (metrics, logs, traces)
- Lead incident response, post-mortems, and blameless RCAs
- Implement chaos engineering and resilience testing
- Reduce toil through automation and self-healing systems
- Mentor engineers on reliability best practices

Required skills
- Extensive Kubernetes and cloud experience (AWS/GCP)
- Prometheus, Grafana, or equivalent observability tools
- Distributed systems fundamentals
- Strong programming skills in Go or Python
- Incident command experience

Nice to have
- Experience with chaos engineering (Chaos Monkey, LitmusChaos)
- Financial services or high-compliance domain
- eBPF or observability deep expertise
- Staff-level engineering impact

Compensation: $160,000 – $220,000 base + equity
""",
    ),
    # ─── Security ──────────────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="cybersecurity-analyst",
        role_title="Cybersecurity Analyst",
        category="Security",
        summary="Protect company infrastructure and respond to security incidents.",
        filename="sample_cybersecurity_analyst.txt",
        parsed_text="""\
Job Title: Cybersecurity Analyst (Tier 2 SOC)
Company: SecureShield — managed security services, 400 employees

About the role
You will work in our Security Operations Centre (SOC) to monitor, detect, and
respond to cybersecurity threats for enterprise clients across regulated industries.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Monitor SIEM alerts and triage potential security incidents (Splunk, Sentinel)
- Conduct threat hunting using IOCs and TTPs from threat intelligence feeds
- Perform digital forensics and incident response (DFIR)
- Write detection rules and tune false positives
- Produce clear incident reports for technical and non-technical audiences
- Collaborate with client security teams on remediation

Required skills
- CompTIA Security+, CySA+, or equivalent certification
- SIEM experience (Splunk, Microsoft Sentinel, or IBM QRadar)
- Understanding of MITRE ATT&CK framework
- Network security fundamentals (firewalls, IDS/IPS, packet analysis)
- Incident response methodology

Nice to have
- OSCP, CEH, or GIAC certifications
- Malware analysis and reverse engineering
- Cloud security (AWS/Azure security services)
- Scripting for automation (Python, PowerShell)

Compensation: $85,000 – $125,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="security-engineer",
        role_title="Security Engineer",
        category="Security",
        summary="Embed security into every stage of the software development lifecycle.",
        filename="sample_security_engineer.txt",
        parsed_text="""\
Job Title: Security Engineer (AppSec / DevSecOps)
Company: TrustLayer — identity management SaaS, Series B, 110 employees

About the role
As a Security Engineer, you will own application security for our product and
platform — from threat modelling and secure code review to penetration testing
and vulnerability management.

Experience Level: Senior (4–7 years)

Responsibilities
- Perform application security reviews, threat modelling, and pen testing
- Implement and maintain SAST, DAST, and SCA tooling in CI/CD pipelines
- Define and enforce secure coding guidelines
- Respond to vulnerability disclosures and security bug reports
- Train and advise engineering teams on security best practices
- Lead security incident response for product vulnerabilities

Required skills
- Web application security (OWASP Top 10, SANS Top 25)
- Penetration testing tools (Burp Suite, OWASP ZAP)
- DevSecOps tooling (Snyk, Semgrep, Trivy, Checkmarx)
- Secure SDLC methodologies
- Scripting proficiency (Python, Bash)

Nice to have
- OSCP, CISSP, or GWEB certification
- AWS / GCP cloud security architecture
- Experience in regulated environments (SOC2, HIPAA, ISO 27001)
- OAuth 2.0, OIDC, and identity security

Compensation: $150,000 – $200,000 base + equity
""",
    ),
    # ─── QA ────────────────────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="qa-engineer",
        role_title="QA Engineer",
        category="Quality",
        summary="Ensure every release ships with confidence through automated and manual testing.",
        filename="sample_qa_engineer.txt",
        parsed_text="""\
Job Title: QA Engineer (SDET)
Company: Fidelity Software — enterprise SaaS, 600 employees

About the role
We are looking for a QA Engineer to build automated test frameworks, define
testing strategy, and partner with developers to catch defects before they
reach production.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Write and maintain automated test suites (unit, integration, E2E)
- Build and extend test automation frameworks (Playwright, Cypress, or Selenium)
- Perform exploratory and regression testing for new features
- Work with developers to reproduce and root-cause defects
- Contribute to CI/CD pipeline quality gates
- Define and track quality metrics (defect escape rate, test coverage)

Required skills
- Test automation with Playwright, Cypress, or Selenium
- API testing (Postman, REST Assured)
- Strong Python or JavaScript for test scripting
- Understanding of testing methodologies (TDD, BDD)
- Bug tracking and test management tools (Jira, TestRail)

Nice to have
- Performance and load testing (k6, Locust, JMeter)
- Mobile testing (Appium)
- AI-assisted testing tools
- Experience with accessibility testing

Compensation: $95,000 – $135,000 base
""",
    ),
    # ─── Mobile Development ────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="ios-developer",
        role_title="iOS Developer",
        category="Mobile",
        summary="Build polished, high-performance native iOS applications for millions of users.",
        filename="sample_ios_developer.txt",
        parsed_text="""\
Job Title: iOS Developer (Senior)
Company: Luma Mobile — consumer app studio, 90 employees

About the role
We build award-winning iOS applications that top the App Store charts. We need
a senior iOS developer who cares deeply about performance, animations, and
the Apple platform ecosystem.

Experience Level: Senior (4–7 years)

Responsibilities
- Build and ship features in Swift and SwiftUI
- Architect and maintain a large, modular iOS codebase
- Implement smooth animations and transitions using SwiftUI and Core Animation
- Optimise app performance, launch time, and battery usage
- Integrate with backend APIs (REST, GraphQL, WebSocket)
- Write unit and UI tests (XCTest)

Required skills
- Expert Swift and SwiftUI (4+ years)
- UIKit knowledge for legacy integration
- Concurrency (async/await, Combine, or Dispatch)
- App Store submission and review process
- Instruments, Xcode debugging, and profiling

Nice to have
- AR/VR features (ARKit, RealityKit)
- Core Data or Realm for local persistence
- Push notifications and deep linking
- App Clips or WidgetKit

Compensation: $145,000 – $195,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="android-developer",
        role_title="Android Developer",
        category="Mobile",
        summary="Craft fast, beautiful Android apps using Kotlin and Jetpack Compose.",
        filename="sample_android_developer.txt",
        parsed_text="""\
Job Title: Android Developer
Company: Orbit Mobile — fintech app, Series A, 60 employees

About the role
Join a small, high-velocity mobile team building a next-generation banking
app for Android. You will own core product features from design handoff to
Play Store release.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Build features using Kotlin and Jetpack Compose
- Implement clean architecture (MVVM, MVI, or Clean Architecture)
- Integrate with RESTful and GraphQL APIs
- Write unit, integration, and instrumented tests
- Handle Android security, biometrics, and keystore APIs
- Optimise performance, ANR rates, and battery consumption

Required skills
- Expert Kotlin (3+ years)
- Jetpack Compose for UI
- Android Jetpack libraries (Room, Navigation, WorkManager)
- Coroutines and Flow for asynchronous programming
- Google Play Console and release process

Nice to have
- Kotlin Multiplatform Mobile (KMM)
- Firebase (Analytics, Crashlytics, Remote Config)
- Accessibility on Android
- Financial or banking app experience

Compensation: $130,000 – $175,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="react-native-developer",
        role_title="React Native Developer",
        category="Mobile",
        summary="Build a cross-platform mobile app that feels truly native on iOS and Android.",
        filename="sample_react_native_developer.txt",
        parsed_text="""\
Job Title: React Native Developer
Company: CrossPlatform Co. — travel app startup, 45 employees

About the role
We are building a cross-platform travel companion app using React Native. You
will own mobile features end-to-end, balancing cross-platform code reuse with
platform-native UX.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Build cross-platform features with React Native (Expo or bare workflow)
- Implement native modules where React Native falls short
- Optimise app performance and smooth 60fps animations (Reanimated)
- Integrate location services, camera, push notifications, and payments
- Write comprehensive tests (Jest, Detox for E2E)
- Submit and manage releases on both App Store and Google Play

Required skills
- React Native (2+ years) with production apps shipped
- TypeScript
- React Navigation and state management (Zustand, Redux, or Jotai)
- React Native Reanimated for fluid animations
- Experience with native iOS and Android build tooling

Nice to have
- Expo ecosystem (EAS Build, EAS Submit)
- GraphQL and Apollo or React Query
- Offline-first architecture
- Maps integration (Mapbox, Google Maps)

Compensation: $115,000 – $160,000 base + equity
""",
    ),
    # ─── Game Development ──────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="game-developer-unity",
        role_title="Unity Game Developer",
        category="Gaming",
        summary="Build immersive, performant 3D game experiences in Unity.",
        filename="sample_unity_developer.txt",
        parsed_text="""\
Job Title: Unity Game Developer (Mid-level)
Company: Warpgate Studios — indie game studio, 30 employees

About the role
We are making a narrative-driven sci-fi RPG and need a Unity developer to
implement gameplay systems, optimise performance, and help ship the game
to PC and console platforms.

Experience Level: Mid-level (2–4 years)

Responsibilities
- Implement gameplay mechanics, AI behaviours, and game systems in Unity / C#
- Write clean, performant C# code adhering to SOLID principles
- Optimise for target hardware (CPU, GPU, memory, draw calls)
- Work with artists and designers in an agile team
- Implement UI systems using Unity UI Toolkit or UGUI
- Debug and profile with Unity Profiler and RenderDoc

Required skills
- C# proficiency (2+ years in Unity)
- Unity engine fundamentals (prefabs, scenes, physics, animation)
- Game architecture patterns (ECS, component-based, state machines)
- Version control with Git in a team environment
- Understanding of shaders and rendering pipeline (URP/HDRP basics)

Nice to have
- Shipped title experience (PC, console, or mobile)
- Unity Jobs System / Burst Compiler
- Shader Graph or HLSL
- Console SDK experience (PlayStation, Xbox, Nintendo)

Compensation: $90,000 – $130,000 base + royalties
""",
    ),
    SampleJobDescriptionFixture(
        id="game-developer-unreal",
        role_title="Unreal Engine Developer",
        category="Gaming",
        summary="Create next-gen game experiences using Unreal Engine 5 and C++.",
        filename="sample_unreal_developer.txt",
        parsed_text="""\
Job Title: Unreal Engine Developer
Company: Nexus Game Works — AAA game studio, 250 employees

About the role
Our team is building a AAA open-world action RPG using Unreal Engine 5. We need
a gameplay programmer who can implement complex systems in Blueprints and C++
and contribute to a large-scale project.

Experience Level: Senior (4–8 years)

Responsibilities
- Implement gameplay systems using Unreal Engine 5 and C++
- Design and maintain Blueprint-to-C++ interfaces for designer tooling
- Work with UE5 features: Nanite, Lumen, Chaos Physics, Procedural Content
- Profile and optimise for frame rate on PC and next-gen consoles
- Collaborate with a large cross-disciplinary team (art, design, QA)
- Document systems clearly for other engineers and designers

Required skills
- C++ proficiency (3+ years in Unreal)
- Unreal Engine 5 (Blueprints, Gameplay Ability System, Animation Blueprint)
- Multiplayer networking (Unreal's replication system) is a plus
- Memory management and low-level performance optimisation
- Experience shipping at least one AAA or AA title

Nice to have
- Procedural animation and physics simulation
- AI behaviour trees in UE5
- Console development (PlayStation 5, Xbox Series X)
- Houdini procedural content generation

Compensation: $120,000 – $170,000 base + bonuses
""",
    ),
    # ─── Embedded / Hardware ───────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="embedded-engineer",
        role_title="Embedded Systems Engineer",
        category="Hardware/Embedded",
        summary="Write firmware for IoT devices that are deployed in harsh real-world environments.",
        filename="sample_embedded_engineer.txt",
        parsed_text="""\
Job Title: Embedded Systems Engineer
Company: IotWave — industrial IoT company, 120 employees

About the role
You will develop firmware for ARM Cortex-M microcontrollers used in industrial
monitoring sensors deployed globally. Reliability, power efficiency, and
real-time performance are non-negotiable.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Write and optimise bare-metal and RTOS firmware in C/C++
- Design and implement communication protocols (UART, SPI, I2C, CAN, BLE)
- Develop device drivers for sensors, displays, and communication modules
- Debug hardware/software interfaces with oscilloscopes and logic analysers
- Maintain and evolve existing RTOS-based firmware (FreeRTOS / Zephyr)
- Work with hardware engineers on PCB bring-up and validation

Required skills
- C and C++ embedded programming (3+ years)
- ARM Cortex-M architecture (STM32, nRF52, or similar)
- RTOS experience (FreeRTOS, Zephyr, or equivalent)
- Communication protocols: UART, SPI, I2C, CAN
- Hardware debug tools (JTAG, oscilloscope, logic analyser)

Nice to have
- Wireless protocols (BLE, LoRa, LTE-M, Zigbee)
- Bootloader development and OTA firmware update
- Power optimisation for battery-powered devices
- Linux device driver development

Compensation: $115,000 – $160,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="firmware-engineer",
        role_title="Firmware Engineer",
        category="Hardware/Embedded",
        summary="Develop safety-critical firmware for medical-grade devices.",
        filename="sample_firmware_engineer.txt",
        parsed_text="""\
Job Title: Firmware Engineer (Medical Devices)
Company: MediCore Systems — medical device manufacturer, 800 employees

About the role
We develop Class II and Class III medical devices. Our Firmware Engineer will
implement safety-critical software under IEC 62304, working alongside hardware
engineers and regulatory affairs specialists.

Experience Level: Senior (5+ years, with medical device experience preferred)

Responsibilities
- Write and validate safety-critical C firmware under IEC 62304
- Implement hardware abstraction layers for sensor and actuator interfaces
- Maintain traceability between requirements, code, and test cases
- Support FDA 510(k) and CE mark submissions with technical documentation
- Conduct peer code reviews and static analysis (PC-lint, Polyspace)

Required skills
- C programming expertise in safety-critical contexts
- Knowledge of IEC 62304 software lifecycle standard
- MISRA C compliance and static analysis tools
- Formal verification and unit testing (Unity, CppUTest)
- Requirements management tools (DOORS, Polarion)

Nice to have
- ISO 13485 and FDA QMS experience
- DSP algorithm implementation (signal filtering, FFT)
- Experience with ARM Cortex-M or Cortex-A devices
- Familiarity with RTOS scheduling analysis

Compensation: $130,000 – $175,000 base + benefits
""",
    ),
    # ─── Business Analysis ──────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="business-analyst",
        role_title="Business Analyst",
        category="Business",
        summary="Bridge business stakeholders and technology teams to deliver the right solutions.",
        filename="sample_business_analyst.txt",
        parsed_text="""\
Job Title: Business Analyst (IT / Digital Transformation)
Company: Transform Consulting — digital transformation consultancy, 450 employees

About the role
As a Business Analyst, you will work with enterprise clients to understand their
business problems, elicit requirements, and define solutions that technology teams
can build.

Experience Level: Mid-level (3–6 years)

Responsibilities
- Facilitate stakeholder workshops and requirements elicitation sessions
- Produce business requirements documents (BRDs), functional specs, and user stories
- Conduct gap analysis, process mapping (BPMN), and as-is / to-be documentation
- Manage requirements traceability and change control
- Work with QA teams to define acceptance criteria and UAT plans
- Support project delivery as the link between business and IT

Required skills
- Business requirements elicitation and documentation
- Process modelling (BPMN, UML use case diagrams)
- User story writing and backlog management
- Jira or Azure DevOps for requirements tracking
- Strong stakeholder management and presentation skills

Nice to have
- CBAP, CCBA, or PMI-PBA certification
- Industry experience (financial services, healthcare, or retail)
- SQL for ad-hoc data queries
- Familiarity with Agile / SAFe delivery

Compensation: $90,000 – $130,000 base + bonus
""",
    ),
    # ─── Additional roles ──────────────────────────────────────────────────
    SampleJobDescriptionFixture(
        id="technical-writer",
        role_title="Technical Writer",
        category="Content",
        summary="Write developer documentation, API references, and guides that developers love.",
        filename="sample_technical_writer.txt",
        parsed_text="""\
Job Title: Technical Writer (Developer Documentation)
Company: Apidocs Inc. — developer tooling company, 80 employees

About the role
We need a Technical Writer who can turn complex API documentation into clear,
actionable guides for developers. You will own our developer portal, SDK docs,
and changelog content.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Write, edit, and maintain API references, tutorials, and quickstart guides
- Collaborate with engineers to document new features accurately
- Maintain the developer portal with clear navigation and search
- Test code samples in documentation to ensure they work
- Gather developer feedback and iterate on documentation quality

Required skills
- Excellent technical writing and editing
- Understanding of REST APIs and ability to read code (Python, TypeScript)
- Docs-as-code tooling (Markdown, Sphinx, MkDocs, or Docusaurus)
- Git and pull request workflow
- Ability to understand complex technical concepts and simplify them

Nice to have
- OpenAPI / Swagger specification experience
- GraphQL documentation
- Video tutorials and screencasting
- SEO for developer content

Compensation: $95,000 – $135,000 base
""",
    ),
    SampleJobDescriptionFixture(
        id="solutions-architect",
        role_title="Solutions Architect",
        category="Engineering",
        summary="Design enterprise-scale cloud architectures and guide clients through technical decisions.",
        filename="sample_solutions_architect.txt",
        parsed_text="""\
Job Title: Solutions Architect
Company: CloudBridge Consulting — AWS Premier Partner, 320 employees

About the role
As a Solutions Architect, you will design cloud solutions for enterprise
clients, serve as the technical authority on pre-sales engagements, and guide
implementation teams through complex architecture decisions.

Experience Level: Senior (6+ years, 3+ in cloud architecture)

Responsibilities
- Design scalable, resilient, and cost-optimised cloud architectures
- Create detailed architecture diagrams, PoCs, and technical proposals
- Present solutions to CTO-level stakeholders and technical audiences
- Define migration strategies for on-premises to cloud transitions
- Provide technical oversight during project delivery
- Hold or be pursuing AWS Solutions Architect Professional certification

Required skills
- AWS or Azure architecture at scale (3+ years)
- Microservices, event-driven, and serverless architectural patterns
- Security architecture (IAM, network segmentation, encryption)
- Strong communication skills for both technical and non-technical audiences
- Experience delivering cloud migrations for enterprise clients

Nice to have
- Multi-cloud strategy experience
- FinOps and cloud cost optimisation
- Enterprise networking (Direct Connect, ExpressRoute, VPN)
- Containers and Kubernetes at scale

Compensation: $150,000 – $210,000 base + client bonuses
""",
    ),
    SampleJobDescriptionFixture(
        id="scrum-master",
        role_title="Scrum Master",
        category="Agile",
        summary="Coach agile teams to deliver continuously and improve their engineering practices.",
        filename="sample_scrum_master.txt",
        parsed_text="""\
Job Title: Scrum Master / Agile Coach
Company: Agility Partners — agile transformation consultancy, 200 employees

About the role
We embed Scrum Masters with client engineering teams to facilitate ceremonies,
remove impediments, and coach teams towards a high-performance agile culture.

Experience Level: Mid-to-senior (3–7 years)

Responsibilities
- Facilitate Scrum ceremonies (sprint planning, daily stand-ups, reviews, retros)
- Coach teams and individuals on agile principles and practices
- Identify and resolve impediments to team velocity
- Protect the team from scope creep and external distractions
- Track and communicate team metrics (velocity, cycle time, burn-down)
- Support the product owner with backlog refinement

Required skills
- Certified ScrumMaster (CSM) or equivalent (PSM I/II)
- Deep understanding of Scrum and Kanban
- Experience facilitating agile ceremonies for software teams
- Conflict resolution and coaching skills
- Jira or Azure DevOps for sprint management

Nice to have
- SAFe Scrum Master (SSM) certification
- Experience scaling agile (SAFe, LeSS, Nexus)
- Technical background in software engineering
- Agile coaching tools (retrospective facilitation)

Compensation: $100,000 – $140,000 base + bonus
""",
    ),
    SampleJobDescriptionFixture(
        id="platform-engineer",
        role_title="Platform Engineer",
        category="Infrastructure",
        summary="Build the internal developer platform that lets 200+ engineers ship 100x faster.",
        filename="sample_platform_engineer.txt",
        parsed_text="""\
Job Title: Platform Engineer (Internal Developer Platform)
Company: Stratos Tech — cloud-native SaaS, Series D, 600 employees

About the role
Our Platform Engineering team builds and operates the internal developer
platform: deployment pipelines, developer experience tooling, environment
management, and self-service infrastructure.

Experience Level: Senior (5+ years)

Responsibilities
- Build and maintain the Internal Developer Platform (IDP) with Backstage
- Implement self-service infrastructure provisioning with Terraform and Crossplane
- Own the developer experience: local development, CI/CD, and deployment
- Define platform SLOs and improve reliability for the engineering organisation
- Evangelise platform adoption and gather developer feedback
- Reduce cognitive load for application engineers

Required skills
- Platform engineering and DevOps expertise
- Kubernetes and Helm for application delivery
- Terraform or Crossplane for infrastructure provisioning
- CI/CD (GitHub Actions, Tekton, or Argo Workflows)
- Developer experience tooling (Backstage, Port)

Nice to have
- FinOps and cost visibility tooling
- Policy-as-code (OPA, Kyverno)
- Observability platform (OpenTelemetry, Grafana stack)
- Internal API and CLI design

Compensation: $160,000 – $215,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="growth-engineer",
        role_title="Growth Engineer",
        category="Engineering",
        summary="Build and run experiments that drive acquisition, activation, and retention.",
        filename="sample_growth_engineer.txt",
        parsed_text="""\
Job Title: Growth Engineer
Company: Ramp SaaS — PLG fintech startup, Series C, 180 employees

About the role
Growth Engineers at Ramp own the technical side of growth experiments: A/B
testing infrastructure, onboarding flows, referral programs, and data pipelines
that power growth analytics.

Experience Level: Mid-level (2–5 years)

Responsibilities
- Build A/B testing and feature flag infrastructure
- Implement high-conversion onboarding flows and activation experiments
- Build and maintain growth data pipelines (funnels, cohort analysis)
- Collaborate with Growth PMs on experiment design and analysis
- Optimise acquisition flows (SEO, landing pages, sign-up conversion)
- Ship product-led growth (PLG) mechanics: virality, referrals, usage-based CTA

Required skills
- Full-stack web development (React + Python or Node.js)
- A/B testing tools (LaunchDarkly, Statsig, Optimizely, or homegrown)
- Analytics tooling (Amplitude, Mixpanel, or Segment)
- SQL for funnel and retention analysis
- Statistical significance and experimentation basics

Nice to have
- SEO and technical web optimisation
- PLG mechanics (viral loops, usage-triggered CTAs)
- Revenue-impact analysis
- Experience at a PLG SaaS company

Compensation: $140,000 – $185,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="developer-advocate",
        role_title="Developer Advocate",
        category="Developer Relations",
        summary="Represent our platform to the developer community and make them successful.",
        filename="sample_developer_advocate.txt",
        parsed_text="""\
Job Title: Developer Advocate
Company: OpenStack Labs — developer API platform, Series B, 100 employees

About the role
As a Developer Advocate, you will be the voice of developers inside the company
and the face of the company to developers. You will create content, build sample
applications, speak at conferences, and gather feedback to shape the product.

Experience Level: Mid-to-senior (3–6 years as a developer)

Responsibilities
- Create tutorials, blog posts, videos, and sample applications
- Present at conferences, meetups, and webinars
- Build and maintain sample apps and quickstart projects on GitHub
- Gather developer feedback and represent it internally to product teams
- Run developer community events and online programs
- Monitor community channels (Discord, Slack, GitHub) and support developers

Required skills
- Hands-on software development experience (2+ years in production code)
- Excellent technical writing and presentation skills
- Comfortable on camera and speaking to audiences
- Experience building API integrations
- Active presence in developer community

Nice to have
- Experience as a developer advocate or technical evangelist
- Open-source contributions
- Podcast or YouTube channel experience
- Strong social media following in developer communities

Compensation: $120,000 – $165,000 base + content bonuses
""",
    ),
    SampleJobDescriptionFixture(
        id="data-platform-engineer",
        role_title="Analytics Engineer",
        category="Data",
        summary="Transform raw warehouse data into reliable, well-modelled data assets for the business.",
        filename="sample_analytics_engineer.txt",
        parsed_text="""\
Job Title: Analytics Engineer
Company: DataLayer — data-as-a-service startup, Series A, 55 employees

About the role
Analytics Engineers bridge data engineering and data analysis. You will own
the transformation layer using dbt, model data for business consumers, and
ensure data quality and documentation.

Experience Level: Mid-level (2–4 years)

Responsibilities
- Build and maintain dbt data models (staging, marts, intermediate layers)
- Write clean, well-tested SQL and dbt macros
- Partner with data analysts to understand modelling needs
- Implement dbt tests, documentation, and freshness checks
- Optimise query performance in Snowflake, BigQuery, or Redshift
- Maintain data lineage and a data catalogue (dbt Docs, Atlan)

Required skills
- Advanced SQL expertise
- dbt Core or dbt Cloud (2+ years)
- Cloud data warehouse (Snowflake, BigQuery, or Redshift)
- Git workflow and code review
- Understanding of dimensional modelling and Kimball methodology

Nice to have
- Python for custom dbt macros or custom materialisations
- Airflow or Prefect for pipeline scheduling
- Looker LookML or Tableau calculated fields
- Data observability tools (Monte Carlo, Great Expectations)

Compensation: $110,000 – $155,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="nlp-engineer",
        role_title="NLP Engineer",
        category="AI/ML",
        summary="Build language understanding systems that power intelligent text features.",
        filename="sample_nlp_engineer.txt",
        parsed_text="""\
Job Title: NLP Engineer
Company: LinguaTech — conversational AI platform, Series B, 140 employees

About the role
We build enterprise-grade NLP systems: document understanding, intent
classification, entity extraction, and conversational AI. You will work on
models that process millions of documents per day.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Design and implement NLP pipelines for text classification, NER, and Q&A
- Fine-tune transformer models (BERT, RoBERTa, T5) on domain-specific data
- Build evaluation datasets, run error analysis, and improve model quality
- Deploy NLP models as low-latency inference services
- Work with product teams to translate language requirements into model capabilities

Required skills
- Python and deep NLP libraries (HuggingFace Transformers, spaCy)
- Experience fine-tuning transformer models
- Text preprocessing, feature engineering, and evaluation methodology
- Understanding of attention mechanisms and modern NLP architectures
- SQL and data manipulation

Nice to have
- LLM prompting and RAG for NLP tasks
- Knowledge graphs and semantic search
- Production NLP serving (TorchServe, TGI, vLLM)
- Multilingual model experience

Compensation: $145,000 – $195,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="robotics-engineer",
        role_title="Robotics Software Engineer",
        category="Hardware/Embedded",
        summary="Program autonomous robots that navigate and interact with the physical world.",
        filename="sample_robotics_engineer.txt",
        parsed_text="""\
Job Title: Robotics Software Engineer
Company: Autonomy Robotics — warehouse automation, Series C, 220 employees

About the role
We build autonomous mobile robots (AMRs) for warehouse logistics. You will
work on the software stack: perception, planning, control, and fleet management
for robots operating in dynamic environments.

Experience Level: Mid-to-senior (3–6 years)

Responsibilities
- Implement and improve motion planning, localisation (SLAM), and navigation
- Develop real-time control systems with hard latency requirements
- Integrate sensor fusion algorithms (LiDAR, cameras, IMU)
- Write ROS 2 nodes and launch configurations
- Contribute to simulation environments (Gazebo, Isaac Sim)
- Collaborate with hardware engineers on robot bring-up and calibration

Required skills
- C++ proficiency for robotics (real-time constraints)
- ROS 2 ecosystem (nodes, topics, services, actions)
- SLAM algorithms or motion planning (MoveIt, Nav2)
- Linux embedded systems experience
- Python for tooling, scripting, and offline analysis

Nice to have
- Computer vision (OpenCV, deep learning-based detection)
- Kalman filtering and sensor fusion
- Safety-critical systems (IEC 61508 or EN 62061)
- Experience with autonomous vehicles or drones

Compensation: $140,000 – $195,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="staff-engineer",
        role_title="Staff Software Engineer",
        category="Engineering",
        summary="Lead technical direction across multiple teams and mentor the next generation of engineers.",
        filename="sample_staff_engineer.txt",
        parsed_text="""\
Job Title: Staff Software Engineer
Company: Horizon Labs — B2B SaaS, Series D, 700 employees

About the role
Staff Engineers at Horizon are technical leaders without direct reports. You
will drive architectural decisions, set engineering standards, and be the
technical mentor for 20+ engineers across three product teams.

Experience Level: Staff / Principal (8+ years)

Responsibilities
- Define technical strategy and architecture for multi-team product areas
- Write detailed architecture decision records (ADRs) and RFCs
- Lead complex cross-team technical initiatives end-to-end
- Mentor senior and mid-level engineers through technical pairing and review
- Identify and eliminate systemic tech debt and reliability gaps
- Represent engineering in product roadmap discussions

Required skills
- Deep software engineering expertise (8+ years, full-stack preferred)
- Proven track record of delivering impactful architectural changes
- Strong written communication for design documents and ADRs
- Experience with distributed systems at scale
- Leadership through influence (no direct reports)

Nice to have
- Experience growing engineers to senior and staff level
- Public speaking, conference talks, or technical blog writing
- Open-source contributions
- IPO / acquisition engineering experience

Compensation: $200,000 – $280,000 base + equity
""",
    ),
    SampleJobDescriptionFixture(
        id="engineering-manager",
        role_title="Engineering Manager",
        category="Management",
        summary="Grow and lead a high-performing engineering team shipping impactful features.",
        filename="sample_engineering_manager.txt",
        parsed_text="""\
Job Title: Engineering Manager
Company: Altitude SaaS — B2B workflow platform, Series C, 400 employees

About the role
We are looking for an Engineering Manager to lead a team of 6–8 engineers
building our core product. You will be half technical leader, half people manager:
keeping the team technically sound, professionally growing, and productively happy.

Experience Level: 5+ years as an engineer, 2+ years in management

Responsibilities
- Manage and grow a team of 6–8 software engineers
- Conduct regular 1:1s, performance reviews, and career coaching
- Partner with the product manager on roadmap planning and trade-offs
- Set technical direction and review high-level system designs
- Remove blockers, manage cross-team dependencies, and escalate risks
- Recruit, hire, and onboard engineers

Required skills
- Former software engineering background (can still contribute technically)
- Experience managing individual contributors in a fast-paced environment
- Strong 1:1 and coaching skills
- Familiarity with delivery metrics and engineering health indicators
- Excellent communication with product, design, and leadership

Nice to have
- Experience scaling teams from 5 to 20+
- Technical depth in backend, infrastructure, or full stack
- Experience with remote or hybrid engineering teams
- Track record of promoting engineers to senior and staff levels

Compensation: $170,000 – $230,000 base + equity
""",
    ),
]


def get_sample_by_id(sample_id: str) -> SampleJobDescriptionFixture | None:
    for sample in SAMPLE_JOB_DESCRIPTIONS:
        if sample.id == sample_id:
            return sample
    return None
