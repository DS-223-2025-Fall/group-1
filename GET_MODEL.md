# How to Get the CatBoost Model File

## Problem
The `catboost_model.cbm` file is a Git LFS pointer (132 bytes) instead of the actual model file (~4.5 MB).

## Solution: Install Git LFS and Pull the File

### Step 1: Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions. After installation, you may need to add Homebrew to your PATH:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

### Step 2: Install Git LFS
```bash
brew install git-lfs
```

### Step 3: Initialize Git LFS
```bash
cd /Users/nareknurijanyan/Desktop/Project_W223/group-1
git lfs install
```

### Step 4: Pull the Model File
```bash
git lfs pull
```

### Step 5: Verify the File
```bash
ls -lh yerevan_pricing/api/model/catboost_model.cbm
```

You should see a file size of approximately **4.5 MB** (not 132 bytes).

### Step 6: Restart the API
```bash
cd yerevan_pricing
docker-compose restart group1_api
```

### Step 7: Test the Forecast
Try forecasting again in the frontend at http://localhost:8501

---

## Alternative: Get Model from Team Member

If Git LFS installation is not possible, ask a team member who has the actual model file to:
1. Share the file (it should be ~4.5 MB)
2. Copy it to: `yerevan_pricing/api/model/catboost_model.cbm`
3. Restart the API: `docker-compose restart group1_api`

---

## Verify It's Working

After getting the model file, test the API:
```bash
curl "http://localhost:8008/predict-price?product_name=Cappuccino&location=Kentron&venue_type=coffee_house&portion_size=medium&age_group=25-34"
```

You should get a JSON response with `predicted_price`, not an error.

