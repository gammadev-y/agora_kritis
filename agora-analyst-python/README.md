# 🧠 Agora Kritis 4.0 - AI Legal Document Analysis

[![Kritis 4.0 Analysis](https://github.com/gammadev-y/agora_kritis/actions/workflows/kritis-analysis.yml/badge.svg)](https://github.com/gammadev-y/agora_kritis/actions/workflows/kritis-analysis.yml)

Kritis 4.0 is an advanced AI-powered legal document analysis system that transforms complex legal texts into clear, understandable summaries. Built for the Agora platform, it provides intelligent extraction, analysis, and knowledge graph generation for Portuguese legal documents.

## ✨ Features

### 🎯 **Kritis 4.0 Enhanced Pipeline**
- **Stage 1**: Enhanced Metadata Extraction with Portuguese date patterns
- **Stage 2**: Contextual Analysis with robust batch processing and retry logic
- **Stage 3**: Intelligent Knowledge Graph with enhanced tagging and cross-references

### 🤖 **AI-Powered Analysis**
- **Conversational Style**: Plain language summaries that anyone can understand
- **Intelligent Tagging**: Automatic categorization and entity extraction
- **Cross-Reference Detection**: Links between related legal documents
- **Robust Error Handling**: 3-tier retry strategy for reliable processing

### 🏗️ **Production Features**
- **GitHub Actions Integration**: Automated workflows for scalable processing
- **Environment Configuration**: Secure secrets management
- **Comprehensive Logging**: Detailed analysis tracking and reporting
- **UUID Validation**: Input sanitization and validation

## 🚀 Quick Start

### GitHub Actions (Recommended)

1. **Set up Repository Secrets**:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: Service role key for database access
   - `SUPABASE_ANON_KEY`: Anonymous key for public access
   - `GEMINI_API_KEY`: Google Gemini API key for AI analysis

2. **Run Analysis**:
   - Go to **Actions** tab in your repository
   - Select **"🧠 Kritis 4.0 - AI Legal Document Analysis"**
   - Click **"Run workflow"**
   - Enter your Source ID (UUID format)
   - Select pipeline stage (or "full-pipeline" for complete analysis)

### Local Development

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/gammadev-y/agora_kritis.git
   cd agora_kritis
   ```

2. **Set up Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your actual credentials
   ```

4. **Run Analysis**:
   ```bash
   # Full Kritis 4.0 Pipeline
   python main.py enhanced-extract --source-id YOUR_SOURCE_ID
   python main.py enhanced-analyze-context --source-id YOUR_SOURCE_ID
   python main.py intelligent-graph --source-id YOUR_SOURCE_ID
   ```

## 📋 Pipeline Stages

### Stage 1: Enhanced Metadata Extraction
```bash
python main.py enhanced-extract --source-id YOUR_SOURCE_ID
```
- Extracts document metadata (titles, numbers, dates)
- Enhanced Portuguese date pattern recognition
- Validates and normalizes extracted data

### Stage 2: Enhanced Analysis with Context
```bash
python main.py enhanced-analyze-context --source-id YOUR_SOURCE_ID
```
- Analyzes articles with preamble context
- Robust batch processing with retry logic
- Conversational-style summaries
- Intelligent entity extraction

### Stage 3: Intelligent Knowledge Graph
```bash
python main.py intelligent-graph --source-id YOUR_SOURCE_ID
```
- Creates law records in database
- Builds article relationships
- Generates intelligent tags
- Creates comprehensive knowledge graph

## 🎨 Kritis Style Guide

Kritis 4.0 follows a human-centric approach to legal document analysis:

### ✅ **Do**
- Use simple, everyday language
- Create bullet points for conditions/rules
- Speak directly to the reader ("you")
- Go straight to the explanation

### ❌ **Don't**
- Use legal jargon or complex terminology
- Start with phrases like "This article is about..."
- Create overly technical explanations
- Use passive voice unnecessarily

### Example Output
**Traditional Legal Text**:
> "O limite para o provimento em cargos públicos, fixado no artigo 4.º do Decreto n.º 16563, não é aplicável aos que antes de excederem a idade se mantenham ao serviço sem interrupção"

**Kritis 4.0 Output**:
> **Limite de idade ignorado em certos casos**
> 
> O limite de idade para cargos públicos é ignorado se:
> - Tiver tido serviço prévio contínuo ao estado; ou
> - Tiver tido interrupções de menos de 60 dias que não foram por sua culpa.

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for admin operations | ✅ |
| `SUPABASE_ANON_KEY` | Anonymous key for public access | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING) | ❌ |
| `MAX_RETRIES` | Maximum retry attempts (default: 3) | ❌ |
| `BATCH_SIZE` | Articles per batch (default: 5) | ❌ |

### GitHub Actions Secrets
Set up the following secrets in your repository settings:
- Repository → Settings → Secrets and variables → Actions

## 📊 Monitoring & Logging

Kritis 4.0 provides comprehensive logging and monitoring:

- **Completion Rates**: Track successful vs failed analyses
- **Processing Times**: Monitor performance metrics
- **Error Handling**: Detailed error reporting with fallback strategies
- **Analysis Quality**: Validation of generated summaries

## 🛠️ Development

### Project Structure
```
agora_kritis/
├── .github/workflows/        # GitHub Actions workflows
├── analysis/                 # Analysis modules
│   ├── kritis_analyzer_v4.py # Main Kritis 4.0 analyzer
│   └── ...                   # Other analysis components
├── lib/                      # Utility libraries
├── main.py                   # CLI entry point
├── requirements.txt          # Python dependencies
└── .env.template            # Environment template
```

### Key Components
- **KritisAnalyzerV4**: Main analysis engine with enhanced features
- **GitHub Actions Workflow**: Automated pipeline execution
- **Environment Management**: Secure configuration handling
- **Error Handling**: Robust retry mechanisms and fallbacks

## 🧪 Testing

### Test with Sample Source ID
```bash
# Use the GitHub Actions workflow or run locally:
python main.py intelligent-graph --source-id 7fd635ce-1a28-44e3-bf13-85b9b29fa610
```

### Validation Tests
The system includes automatic validation for:
- UUID format validation
- Environment variable presence
- Database connectivity
- API key authentication
- Analysis completeness

## 📚 Documentation

- **PROD5.md**: Kritis 4.0 specifications and requirements
- **PROD6.md**: Style guide and persona definition
- **Analysis Pipeline**: Detailed technical documentation in code comments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Agora platform for legal document analysis.

## 🆘 Support

For issues and questions:
1. Check the GitHub Actions logs for detailed error information
2. Review the environment configuration
3. Ensure all required secrets are properly set
4. Validate source ID format (must be valid UUID)

---

**Made with ❤️ for the Agora Platform**