# ML Model Setup Guide

This guide explains how to download and set up the CatBoost ML model for the Yerevan Pricing API.

## Quick Start

Run the setup script:

```bash
./setup_model.sh
```

This script will:
1. Check if Git LFS is installed
2. Initialize Git LFS in the repository
3. Pull the actual model file (not just the pointer)
4. Verify the model file is correct

## Manual Setup

If you prefer to set up manually:

### 1. Install Git LFS

**macOS:**
```bash
brew install git-lfs
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install git-lfs
```

**Windows:**
Download from [https://git-lfs.github.com/](https://git-lfs.github.com/)

### 2. Initialize Git LFS

```bash
git lfs install
```

### 3. Pull the Model File

```bash
git lfs pull
```

Or if you need to fetch from remote first:

```bash
git fetch
git lfs pull
```

### 4. Verify the Model

Check that the model file exists and is the correct size:

```bash
ls -lh api/model/catboost_model.cbm
```

The file should be **at least 1 MB** (typically 4-5 MB). If it's only ~130 bytes, it's still a Git LFS pointer and you need to pull the actual file.

## Troubleshooting

### Model file is still a pointer (small file size)

If the model file is only ~130 bytes, it means Git LFS didn't download the actual file:

1. **Check Git LFS is installed:**
   ```bash
   git lfs version
   ```

2. **Re-initialize Git LFS:**
   ```bash
   git lfs install
   git lfs pull
   ```

3. **Check LFS file status:**
   ```bash
   git lfs ls-files
   ```

4. **Force pull specific file:**
   ```bash
   git lfs fetch
   git lfs checkout api/model/catboost_model.cbm
   ```

### API returns "Model file is a Git LFS pointer" error

This means the API detected the file is still a pointer. Run the setup script or follow the manual steps above.

### Git LFS certificate errors

If you get certificate errors when pulling:

```bash
# For GitHub, you can temporarily disable SSL verification (not recommended for production)
git config --global http.sslVerify false

# Or fix your certificate path
git config --global http.sslCAInfo /path/to/cert.pem
```

## Model File Location

The model file should be located at:
```
api/model/catboost_model.cbm
```

This path is configured in `api/main.py` and is automatically mounted in the Docker container.

## Testing

After setting up the model, test it:

1. **Start the API:**
   ```bash
   docker-compose up -d group1_api
   ```

2. **Check health:**
   ```bash
   curl http://localhost:8008/health
   ```

3. **Test prediction:**
   ```bash
   curl 'http://localhost:8008/predict-price?product_name=Cappuccino&location=Kentron&venue_type=restaurant&portion_size=medium&age_group=25-34'
   ```

## Additional Resources

- [Git LFS Documentation](https://git-lfs.github.com/)
- [CatBoost Documentation](https://catboost.ai/)

