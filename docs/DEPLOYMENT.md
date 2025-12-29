# Deployment Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Google Generative AI API key (optional)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:
```
GOOGLE_API_KEY=your_google_api_key_here
```

## Local Deployment

### Run Application

```bash
python app.py
```

Or use launcher:
```bash
run_scheduler.bat  # Windows
```

Access at: **http://localhost:7860**

## Network Deployment

To make accessible on local network:

Already configured in code:
```python
app.launch(
    server_name="0.0.0.0",  # Network access
    server_port=7860,
    share=False
)
```

Access from other machines: `http://<your-ip>:7860`

## Testing

Run integration tests:
```bash
python test_scheduler.py
```

Expected output:
- ✓ Sample Excel created
- ✓ Interns loaded
- ✓ Schedule generated
- ✓ Validation passed
- ✓ Output files created

## Production Checklist

### Pre-Deployment
- [ ] All dependencies installed
- [ ] Google API key configured
- [ ] Tests pass successfully
- [ ] Real data tested
- [ ] PDF reports verified

### Deployment
- [ ] App launches without errors
- [ ] All 6 tabs functional
- [ ] God View renders correctly
- [ ] Bottleneck analysis works
- [ ] Excel export successful
- [ ] PDF export successful

### Post-Deployment
- [ ] Monitor performance
- [ ] Collect user feedback
- [ ] Track success metrics
- [ ] Document issues

## Success Metrics

Track these after deployment:

| Metric | Target | Measure |
|--------|--------|---------|
| Schedule generation time | <30 min | Timer |
| Manual override rate | <5% | User tracking |
| Audit acceptance | 100% | Regulator feedback |
| Bottleneck prevention | 90%+ | Actual vs predicted |

## Troubleshooting

### Common Issues

**Module not found:**
```bash
pip install -r requirements.txt
```

**Port already in use:**
Change port in code or stop other process

**Plots not rendering:**
```bash
pip install plotly kaleido
```

**PDF generation fails:**
```bash
pip install reportlab
```

**Google API errors:**
- Check API key in `.env`
- App works without it (no AI suggestions)

## Monitoring

### Log Files
- Check terminal output for errors
- Solver progress logged during generation

### Performance
- Monitor solve times
- Track memory usage for large datasets
- Watch for timeout issues

## Backup

### Data Backup
- Excel files (input/output)
- PDF audit reports
- Configuration files

### Code Backup
- Git repository recommended
- Version control for updates

## Updates

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Configuration Updates
Edit `config.py` for:
- Station definitions
- Capacity limits
- Business rules

## Support

### Documentation
- README.md - Overview
- QUICKSTART.md - Setup guide
- ARCHITECTURE.md - Technical details
- This file - Deployment

### Getting Help
1. Check documentation
2. Review error messages
3. Test with sample data
4. Verify configuration

## Cloud Deployment (Optional)

### Hugging Face Spaces
```bash
# Deploy to Hugging Face Spaces
# Follow their Gradio app deployment guide
```

### Docker (Future)
```dockerfile
FROM python:3.8
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app_scheduler_complete.py"]
```

## Maintenance

### Regular Tasks
- Update dependencies monthly
- Review and adjust constraints
- Backup output files
- Monitor performance

### When to Update
- New station requirements
- Changed capacity limits
- Modified business rules
- Bug fixes

## Next Steps

After successful deployment:
1. Train users
2. Collect feedback
3. Measure metrics
4. Plan Phase 2 (Resident AI Companion)
