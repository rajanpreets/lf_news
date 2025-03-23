import React, { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Grid,
  Paper,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

const App = () => {
  const [drugs, setDrugs] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analyzeDrugs = async () => {
    if (!drugs.trim()) {
      setError('Please enter at least one drug name');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/analyze`,
        { drugs: drugs.split(',').map(d => d.trim()) }
      );
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze drugs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#1976d2' }}>
          Pharma News Analyzer
        </Typography>
        
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={9}>
            <TextField
              fullWidth
              label="Enter drug names (comma-separated)"
              variant="outlined"
              value={drugs}
              onChange={(e) => setDrugs(e.target.value)}
              placeholder="Example: Jardiance, Ozempic"
              disabled={loading}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              onClick={analyzeDrugs}
              disabled={loading}
              sx={{ height: 56 }}
            >
              {loading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : 'Analyze'}
            </Button>
          </Grid>
        </Grid>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {results.map((drugData, index) => (
        <Accordion key={index} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {drugData.molecule}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Section title="Latest Summary" content={drugData.latest_summary} />
                <Section title="Mechanism of Action" content={drugData.moa} />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ color: '#2e7d32' }}>
                  News Categories
                </Typography>
                <Grid container spacing={3}>
                  <CategorySection 
                    title="Regulatory News 📜" 
                    content={drugData.regulatory_news}
                    color="#1976d2"
                  />
                  <CategorySection
                    title="Clinical News 🏥"
                    content={drugData.clinical_news}
                    color="#d32f2f"
                  />
                  <CategorySection
                    title="Commercial News 💼"
                    content={drugData.commercial_news}
                    color="#ed6c02"
                  />
                </Grid>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      ))}
    </Container>
  );
};

const Section = ({ title, content }) => (
  <Paper elevation={1} sx={{ p: 3, mb: 3, backgroundColor: '#f5f5f5' }}>
    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
      {title}
    </Typography>
    <Typography variant="body1" whiteSpace="pre-wrap" sx={{ lineHeight: 1.6 }}>
      {content}
    </Typography>
  </Paper>
);

const CategorySection = ({ title, content, color }) => (
  <Grid item xs={12} md={4}>
    <Paper sx={{ 
      p: 2, 
      height: '100%', 
      borderLeft: `4px solid ${color}`,
      backgroundColor: `${color}10`
    }}>
      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, color }}>
        {title}
      </Typography>
      <Typography variant="body2" whiteSpace="pre-wrap" sx={{ color: '#616161' }}>
        {content}
      </Typography>
    </Paper>
  </Grid>
);

export default App;
