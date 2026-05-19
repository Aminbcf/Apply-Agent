# SonarQube Setup Guide

## Cloud Setup (Recommended for CI/CD)

You have connected SonarQube Cloud to this repository. The GitHub Actions workflow will automatically scan pull requests and pushes.

### Configuration

1. **GitHub Repository Secrets** (required):
   - `SONAR_TOKEN`: Your SonarQube Cloud token from https://sonarqube.cloud/account/security/
   - `SONAR_ORGANIZATION`: Your SonarQube Cloud organization key (visible in the dashboard)

2. **Repository Variables** (optional):
   - None required for Cloud setup; the workflow uses defaults.

3. **Sonar Project Config**:
   - `sonar-project.properties` in the repository root configures source paths and exclusions.
   - The project key and organization link is managed through SonarQube Cloud UI.

### Workflow Execution

The CI pipeline in `.github/workflows/ci.yml` runs on:
- Push to `main` or `master` branch
- Pull requests

It validates Python and Node dependencies, builds the frontend, then scans with SonarQube Cloud.

### Viewing Results

- Dashboard: https://sonarqube.cloud/dashboard?id=apply-agent
- Issues: https://sonarqube.cloud/project/issues?id=apply-agent

---

## Local SonarQube Setup (Development)

If you prefer to run SonarQube locally for testing before pushing:

### Start Local SonarQube

```bash
cd infra/sonarqube
docker compose up -d
```

Access at http://localhost:9000 (default credentials: admin/admin).

### Generate Local Token

1. Log in to http://localhost:9000
2. Go to **My Account → Security → Generate Tokens**
3. Create a token and copy it
4. Run a scan locally:
   ```bash
   sonar-scanner \
     -Dsonar.projectKey=apply-agent \
     -Dsonar.sources=src/backend,src/frontend \
     -Dsonar.host.url=http://localhost:9000 \
     -Dsonar.login=<your-token>
   ```

### Stop Local SonarQube

```bash
cd infra/sonarqube
docker compose down
```

### Clean Up Volumes (optional)

```bash
docker volume rm sonarqube_sonar-db sonarqube_sonar-data sonarqube_sonar-extensions
```
