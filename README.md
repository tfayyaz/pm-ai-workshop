# Excuse Email Draft Tool

A modern web application that generates creative excuse emails using Databricks Model Serving LLM. Built with FastAPI backend and React frontend, designed to work seamlessly both locally and on Databricks Apps.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)

## ✨ Features

- **🎭 Multiple Categories**: Running Late, Missed Meeting, Deadline, WFH/OOO, Social, Travel
- **🎨 Tone Selection**: Sincere, Playful, Corporate
- **📊 Seriousness Scale**: 1 (Very Silly) to 5 (Very Serious)
- **🤖 AI-Powered**: Uses Databricks Model Serving LLM
- **💅 Modern UI**: Beautiful, responsive design with Tailwind CSS
- **📋 Copy to Clipboard**: One-click copy functionality
- **🚀 Production Ready**: Works locally and deploys to Databricks Apps

## 📁 Project Structure

```
pm-ai-workshop/
├── app.yaml              # Databricks Apps configuration
├── requirements.txt      # Python dependencies
├── src/
│   └── app.py           # FastAPI backend entry point
├── public/
│   └── index.html       # Single-page React + Tailwind frontend
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Databricks workspace with Model Serving enabled
- Databricks Personal Access Token

### Local Development

1. **Clone and Navigate**
   ```bash
   cd pm-ai-workshop
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   DATABRICKS_API_TOKEN=your_actual_token_here
   DATABRICKS_ENDPOINT_URL=https://your-workspace.cloud.databricks.com/serving-endpoints/your-endpoint/invocations
   ```

4. **Run the Application**
   ```bash
   python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open in Browser**
   ```
   http://localhost:8000
   ```

## 🌐 Databricks Apps Deployment

### Step 1: Configure App Secret

In your Databricks workspace, create an App secret:

```bash
databricks apps secrets create-secret \
  --app-name excuse-gen-app \
  --key databricks_token \
  --value "your_databricks_personal_access_token"
```

Or via UI:
1. Navigate to your App in Databricks workspace
2. Go to "Secrets" section
3. Add secret with key: `databricks_token`
4. Value: Your Databricks Personal Access Token

### Step 2: Deploy the App

```bash
# Using Databricks CLI
databricks apps deploy excuse-gen-app --source-code-path .

# Or using the Databricks UI
# 1. Go to Workspace > Apps
# 2. Click "Create App"
# 3. Upload your source code directory
# 4. Click "Deploy"
```

### Step 3: Access Your App

Once deployed, your app will be available at:
```
https://<workspace-url>/apps/excuse-gen-app
```

## 🎮 How to Use

1. **Select Category**: Choose the type of excuse you need
2. **Choose Tone**: Pick between Sincere, Playful, or Corporate
3. **Adjust Seriousness**: Slide from 1 (silly) to 5 (serious)
4. **Fill Details**: 
   - Recipient name
   - Your name (sender)
   - ETA or timeframe
5. **Generate**: Click "Generate Excuse" button
6. **Copy**: Use "Copy to Clipboard" to copy the generated email

## 🛠️ Technical Details

### Backend (FastAPI)

- **Framework**: FastAPI with async support
- **CORS**: Enabled for React frontend
- **Logging**: Comprehensive request/response logging
- **Health Checks**: Multiple endpoints (`/health`, `/healthz`, `/ready`, `/ping`)
- **Metrics**: Prometheus-compatible metrics endpoint
- **Error Handling**: Graceful error handling with meaningful messages

### Frontend (React + Tailwind)

- **Single-File App**: No build process required
- **CDN Dependencies**: React, ReactDOM, Babel via CDN
- **Responsive Design**: Mobile-first approach
- **State Management**: React hooks
- **Loading States**: Visual feedback during API calls
- **Error Handling**: User-friendly error messages

### LLM Integration

- **Endpoint**: Databricks Model Serving
- **Format**: OpenAI-compatible API
- **Prompts**: Context-aware, structured prompts
- **Response Parsing**: Robust JSON parsing with fallbacks

## 📡 API Endpoints

### Main Endpoints

- `POST /api/generate-excuse` - Generate excuse email
  ```json
  {
    "category": "Running Late",
    "tone": "Playful",
    "seriousness": 3,
    "recipient_name": "Alex",
    "sender_name": "Mona",
    "eta_when": "15 minutes"
  }
  ```

### Monitoring Endpoints

- `GET /health` - Health check
- `GET /healthz` - Health check (Kubernetes style)
- `GET /ready` - Readiness check
- `GET /ping` - Simple ping (returns "pong")
- `GET /metrics` - Prometheus metrics
- `GET /debug` - Debug configuration info

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABRICKS_API_TOKEN` | Your Databricks PAT | Yes | - |
| `DATABRICKS_ENDPOINT_URL` | Model Serving endpoint | Yes | See app.yaml |
| `PORT` | Server port | No | 8000 |
| `HOST` | Server host | No | 0.0.0.0 |

### app.yaml Configuration

```yaml
command: [
  "uvicorn",
  "src.app:app",
  "--host", "0.0.0.0",
  "--port", "8000"
]

env:
  - name: 'DATABRICKS_API_TOKEN'
    valueFrom: databricks_token  # References App secret
  - name: 'DATABRICKS_ENDPOINT_URL'
    value: "https://your-endpoint-url"
  - name: 'PORT'
    value: "8000"
  - name: 'HOST'
    value: "0.0.0.0"
```

## 🐛 Troubleshooting

### Issue: "DATABRICKS_API_TOKEN not configured"

**Solution**: Ensure your `.env` file exists and contains a valid token, or that the App secret is configured in Databricks Apps.

### Issue: "Could not find index.html"

**Solution**: Verify the `public/` directory exists and contains `index.html`. Check file permissions.

### Issue: "LLM request timed out"

**Solution**: 
- Check your network connection
- Verify the endpoint URL is correct
- Ensure your Databricks token has access to the Model Serving endpoint

### Issue: Port 8080 instead of 8000

**Solution**: Databricks Apps requires port 8000. Ensure `app.yaml` specifies port 8000, not 8080.

### Issue: CORS errors in browser

**Solution**: The FastAPI backend should have CORS middleware enabled (already configured in `src/app.py`).

## 📊 Example Use Cases

### Running Late to Meeting
- **Category**: Running Late
- **Tone**: Sincere
- **Seriousness**: 4
- **Result**: Professional apology with clear ETA

### Missed Deadline
- **Category**: Deadline
- **Tone**: Corporate
- **Seriousness**: 5
- **Result**: Formal acknowledgment with recovery plan

### Social Event Excuse
- **Category**: Social
- **Tone**: Playful
- **Seriousness**: 2
- **Result**: Light-hearted excuse with humor

## 🔒 Security Best Practices

- ✅ Use `valueFrom` for secrets in `app.yaml`
- ✅ Never commit `.env` files
- ✅ Rotate access tokens regularly
- ✅ Use least-privilege tokens
- ✅ Enable HTTPS in production

## 📈 Performance

- **Response Time**: ~2-5 seconds (depends on LLM)
- **Concurrent Requests**: Supports async handling
- **File Size**: All files under 10MB (Databricks Apps requirement)

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🙏 Acknowledgments

- **Databricks** for Model Serving platform
- **FastAPI** for the excellent web framework
- **React** for the UI library
- **Tailwind CSS** for beautiful styling

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check Databricks documentation for Model Serving
- Review FastAPI documentation for backend questions

## 🎯 Roadmap

- [ ] Add more email categories
- [ ] Support for email templates
- [ ] Email preview with formatting
- [ ] Export to different formats (PDF, HTML)
- [ ] User preferences and history
- [ ] Multiple LLM provider support

---

**Built with ❤️ using FastAPI, React, and Databricks**

*Last Updated: November 2025*
