# GitHub Actions Workflows

This directory contains CI/CD workflows for the Grid Image Generator MCP Server.

## Workflows

### `ci.yml` - Continuous Integration
- **Triggers**: Push and pull requests to main/master/develop branches
- **Purpose**: Lint code, check syntax, and run tests
- **Runs on**: Ubuntu latest

### `docker-build.yml` - Docker Build and Push
- **Triggers**: 
  - Push to main/master branches
  - Tag pushes (v*)
  - Pull requests to main/master
  - Manual dispatch
- **Purpose**: Build and push Docker images to GitHub Container Registry
- **Features**:
  - Multi-platform builds (amd64, arm64)
  - Automatic tagging (branch, SHA, semver)
  - Docker layer caching

### `release.yml` - Release Workflow
- **Triggers**: 
  - GitHub release published
  - Manual dispatch with version input
- **Purpose**: Build and push versioned Docker images for releases

## Container Registry

Images are pushed to: `ghcr.io/<repository>/<image-name>`

## Secrets

No additional secrets are required. The workflows use the built-in `GITHUB_TOKEN` for authentication with GitHub Container Registry.

