
# STEP 2: Import all necessary libraries
import streamlit as st
import requests 
import json
import datetime
import time
import os
import re
import hashlib
import random
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from dataclasses import dataclass, asdict
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict, Counter
import base64
from io import BytesIO
# For AI/LLM integration
try:
    import openai
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# For web scraping
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# For text processing
try:
    from textblob import TextBlob
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    HAS_TEXT_PROCESSING = True
except ImportError:
    HAS_TEXT_PROCESSING = False

print("✅ All imports completed successfully!")

# STEP 3: Configure Streamlit App
st.set_page_config(
    page_title="🤖 AI Job Search Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "# AI Job Search Assistant\nYour intelligent job hunting companion!"
    }
)

# STEP 4: Custom CSS Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }

    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #fafafa;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .job-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }

    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .skill-tag {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }

    .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .status-active { background-color: #4caf50; }
    .status-pending { background-color: #ff9800; }
    .status-inactive { background-color: #f44336; }
</style>
""", unsafe_allow_html=True)

# STEP 5: Data Classes and Models
@dataclass
class JobResult:
    """Enhanced job result data structure"""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    source: str = "Unknown"
    employment_type: str = "Full-time"
    skills_required: List[str] = None
    experience_level: str = "Mid-level"
    company_size: Optional[str] = None
    industry: Optional[str] = None
    job_id: Optional[str] = None
    application_deadline: Optional[str] = None
    remote_friendly: bool = False
    benefits: List[str] = None
    rating: float = 0.0

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'user' or 'bot'
    content: str
    timestamp: datetime.datetime
    message_type: str = "text"  # 'text', 'job_results', 'analysis'
    metadata: Dict = None

@dataclass
class UserProfile:
    """User profile for personalized recommendations"""
    name: str = ""
    email: str = ""
    skills: List[str] = None
    experience_level: str = "Entry"
    preferred_locations: List[str] = None
    preferred_salary_min: int = 0
    preferred_salary_max: int = 0
    preferred_industries: List[str] = None
    job_preferences: Dict = None

# STEP 6: Enhanced Job Search Engine
class AdvancedJobSearchEngine:
    """Advanced job search with multiple sources and AI integration"""

    def __init__(self):
        # API Keys (set these in your environment)
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

        # Job boards and their search patterns
        self.job_boards = {
            'indeed': 'https://www.indeed.com/jobs?q={query}&l={location}',
            'linkedin': 'https://www.linkedin.com/jobs/search/?keywords={query}&location={location}',
            'glassdoor': 'https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}&locT=C&locId={location}',
            'monster': 'https://www.monster.com/jobs/search/?q={query}&where={location}',
            'ziprecruiter': 'https://www.ziprecruiter.com/Jobs/{query}/{location}',
            'careerbuilder': 'https://www.careerbuilder.com/jobs?keywords={query}&location={location}'
        }

        # Initialize AI chat if available
        self.ai_chat = None
        if HAS_OPENAI and self.openai_api_key:
            try:
                self.ai_chat = ChatOpenAI(
                    openai_api_key=self.openai_api_key,
                    model_name="gpt-3.5-turbo",
                    temperature=0.7
                )
            except Exception as e:
                st.warning(f"AI chat initialization failed: {e}")

    def search_google_jobs_advanced(self, query: str, location: str = "",
                                  filters: Dict = None) -> List[JobResult]:
        """Advanced Google Jobs search with filters"""
        jobs = []
        try:
            if not self.serpapi_key:
                return self._generate_enhanced_mock_jobs(query, location, "Google Jobs")

            # Build search parameters
            params = {
                'engine': 'google_jobs',
                'q': query,
                'location': location,
                'api_key': self.serpapi_key,
                'hl': 'en',
                'num': 20
                }

            # Add filters if provided
            if filters:
                if filters.get('date_posted'):
                    params['date_posted'] = filters['date_posted']
                if filters.get('employment_type'):
                    params['employment_type'] = filters['employment_type']
                if filters.get('experience_level'):
                    params['experience_level'] = filters['experience_level']

            response = requests.get("https://serpapi.com/search", params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                jobs_results = data.get('jobs_results', [])

                for job in jobs_results:
                    # Extract enhanced job information
                    job_result = JobResult(
                        title=job.get('title', 'N/A'),
                        company=job.get('company_name', 'N/A'),
                        location=job.get('location', 'N/A'),
                        description=self._clean_description(job.get('description', 'N/A')),
                        url=job.get('share_link', '#'),
                        salary=self._extract_salary_info(job.get('detected_extensions', {})),
                        posted_date=job.get('detected_extensions', {}).get('posted_at', 'N/A'),
                        source='Google Jobs',
                        employment_type=self._extract_employment_type(job),
                        skills_required=self._extract_skills_from_description(job.get('description', '')),
                        experience_level=self._determine_experience_level(job.get('title', '')),
                        job_id=job.get('job_id', ''),
                        remote_friendly=self._is_remote_job(job),
                        benefits=self._extract_benefits(job.get('description', '')),
                        rating=random.uniform(3.5, 5.0)  # Mock rating
                    )
                    jobs.append(job_result)

            return jobs

        except Exception as e:
            st.error(f"Google Jobs search error: {e}")
            return self._generate_enhanced_mock_jobs(query, location, "Google Jobs")

    def search_multiple_sources(self, query: str, location: str = "",
                              sources: List[str] = None) -> Dict[str, List[JobResult]]:
        """Search multiple job sources simultaneously"""
        if sources is None:
            sources = ['google_jobs', 'indeed', 'linkedin', 'glassdoor']

        results = {}

        for source in sources:
            try:
                if source == 'google_jobs':
                    results[source] = self.search_google_jobs_advanced(query, location)
                elif source == 'adzuna' and self.adzuna_app_id:
                    results[source] = self._search_adzuna(query, location)
                else:
                    # Mock results for other sources
                    results[source] = self._generate_enhanced_mock_jobs(
                        query, location, source.title()
                    )
            except Exception as e:
                st.warning(f"Error searching {source}: {e}")
                results[source] = []

        return results

    def _search_adzuna(self, query: str, location: str) -> List[JobResult]:
        """Search Adzuna API"""
        jobs = []
        try:
            if not (self.adzuna_app_id and self.adzuna_app_key):
                return self._generate_enhanced_mock_jobs(query, location, "Adzuna")

            # Adzuna API endpoint
            country = 'us'  # Can be made configurable
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

            params = {
                'app_id': self.adzuna_app_id,
                'app_key': self.adzuna_app_key,
                'what': query,
                'where': location,
                'results_per_page': 20,
                'sort_by': 'relevance'
            }

            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                job_results = data.get('results', [])

                for job in job_results:
                    job_result = JobResult(
                        title=job.get('title', 'N/A'),
                        company=job.get('company', {}).get('display_name', 'N/A'),
                        location=job.get('location', {}).get('display_name', 'N/A'),
                        description=self._clean_description(job.get('description', 'N/A')),
                        url=job.get('redirect_url', '#'),
                        salary=self._format_salary(job.get('salary_min'), job.get('salary_max')),
                        posted_date=job.get('created', 'N/A'),
                        source='Adzuna',
                        skills_required=self._extract_skills_from_description(job.get('description', '')),
                        experience_level=self._determine_experience_level(job.get('title', '')),
                        job_id=job.get('id', ''),
                        remote_friendly=self._is_remote_job(job),
                        rating=random.uniform(3.0, 5.0)
                    )
                    jobs.append(job_result)

            return jobs

        except Exception as e:
            st.error(f"Adzuna search error: {e}")
            return self._generate_enhanced_mock_jobs(query, location, "Adzuna")

    def _generate_enhanced_mock_jobs(self, query: str, location: str, source: str) -> List[JobResult]:
        """Generate realistic mock job data with enhanced features"""
        companies = [
            {"name": "Google", "industry": "Technology", "size": "Large", "rating": 4.4},
            {"name": "Microsoft", "industry": "Technology", "size": "Large", "rating": 4.3},
            {"name": "Amazon", "industry": "E-commerce/Cloud", "size": "Large", "rating": 3.9},
            {"name": "Apple", "industry": "Technology", "size": "Large", "rating": 4.2},
            {"name": "Meta", "industry": "Social Media", "size": "Large", "rating": 4.1},
            {"name": "Netflix", "industry": "Entertainment", "size": "Medium", "rating": 4.2},
            {"name": "Tesla", "industry": "Automotive/Energy", "size": "Large", "rating": 3.8},
            {"name": "Spotify", "industry": "Music/Technology", "size": "Medium", "rating": 4.1},
            {"name": "Airbnb", "industry": "Travel/Technology", "size": "Medium", "rating": 4.0},
            {"name": "Uber", "industry": "Transportation", "size": "Large", "rating": 3.7},
            {"name": "Salesforce", "industry": "Software", "size": "Large", "rating": 4.3},
            {"name": "Adobe", "industry": "Software", "size": "Large", "rating": 4.2},
            {"name": "Zoom", "industry": "Communication", "size": "Medium", "rating": 4.0},
            {"name": "Slack", "industry": "Productivity", "size": "Medium", "rating": 4.1},
            {"name": "Shopify", "industry": "E-commerce", "size": "Medium", "rating": 4.2}
        ]

        job_titles = [
            f"{query} Engineer", f"Senior {query} Developer", f"{query} Specialist",
            f"Lead {query} Architect", f"{query} Consultant", f"Principal {query} Engineer",
            f"{query} Manager", f"Staff {query} Engineer", f"Junior {query} Developer",
            f"{query} Analyst", f"{query} Coordinator", f"Head of {query}"
        ]

        locations = [
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO",
            "Remote", "Atlanta, GA", "Miami, FL", "Portland, OR"
        ]

        skills_database = {
            'python': ['Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'NumPy', 'SQL'],
            'javascript': ['JavaScript', 'React', 'Node.js', 'Vue.js', 'Angular', 'TypeScript'],
            'data': ['SQL', 'Python', 'R', 'Tableau', 'Power BI', 'Excel', 'Statistics'],
            'marketing': ['SEO', 'Google Analytics', 'Social Media', 'Content Strategy'],
            'design': ['Figma', 'Adobe Creative Suite', 'Sketch', 'Prototyping', 'UI/UX'],
            'devops': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform', 'Jenkins']
        }

        benefits = [
            'Health Insurance', 'Dental Insurance', 'Vision Insurance',
            '401(k) Matching', 'Remote Work Options', 'Flexible Hours',
            'Professional Development', 'Stock Options', 'Unlimited PTO',
            'Gym Membership', 'Free Meals', 'Transportation Stipend'
        ]

        jobs = []
        num_jobs = random.randint(8, 15)

        for i in range(num_jobs):
            company = random.choice(companies)
            job_location = location if location else random.choice(locations)

            # Generate realistic salary ranges
            base_salary = random.randint(60, 200) * 1000
            salary_range = f"${base_salary:,} - ${base_salary + random.randint(20, 50) * 1000:,}"

            # Select relevant skills
            relevant_skills = []
            for skill_category, skills in skills_database.items():
                if skill_category.lower() in query.lower():
                    relevant_skills.extend(random.sample(skills, min(3, len(skills))))

            if not relevant_skills:
                relevant_skills = random.sample(
                    [skill for skills in skills_database.values() for skill in skills], 4
                )

            # Generate job description
            description = self._generate_job_description(query, company['name'], relevant_skills)

            job = JobResult(
                title=random.choice(job_titles),
                company=company['name'],
                location=job_location,
                description=description,
                url=f"https://example.com/jobs/{i}",
                salary=salary_range,
                posted_date=(datetime.date.today() -
                           datetime.timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                source=source,
                employment_type=random.choice(['Full-time', 'Part-time', 'Contract', 'Internship']),
                skills_required=relevant_skills,
                experience_level=random.choice(['Entry', 'Mid', 'Senior', 'Lead']),
                company_size=company['size'],
                industry=company['industry'],
                job_id=f"{source.lower()}_{i}_{hash(query) % 10000}",
                remote_friendly='Remote' in job_location or random.choice([True, False]),
                benefits=random.sample(benefits, random.randint(3, 6)),
                rating=company['rating']
            )

            jobs.append(job)

        return jobs

    def _generate_job_description(self, role: str, company: str, skills: List[str]) -> str:
        """Generate realistic job descriptions"""
        templates = [
            f"We are seeking a talented {role} to join {company}'s innovative team. "
            f"You'll work with cutting-edge technologies including {', '.join(skills[:3])} "
            f"to build scalable solutions that impact millions of users worldwide.",

            f"Join {company} as a {role} and help shape the future of technology. "
            f"This role requires expertise in {', '.join(skills[:3])} and offers "
            f"excellent growth opportunities in a collaborative environment.",

            f"{company} is looking for a passionate {role} to contribute to our "
            f"next-generation platform. Experience with {', '.join(skills[:3])} "
            f"is essential, along with strong problem-solving skills.",

            f"Exciting opportunity at {company} for a {role}! You'll be working "
            f"on innovative projects using {', '.join(skills[:3])} while "
            f"collaborating with world-class engineers and designers."
        ]

        return random.choice(templates)

    # Utility methods
    def _clean_description(self, description: str) -> str:
        """Clean and format job description"""
        if not description or description == 'N/A':
            return 'No description available'

        # Remove HTML tags
        clean_desc = re.sub(r'<[^>]+>', '', description)
        # Remove extra whitespace
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        # Limit length
        return clean_desc[:800] + '...' if len(clean_desc) > 800 else clean_desc

    def _extract_salary_info(self, extensions: Dict) -> str:
        """Extract salary information"""
        salary = extensions.get('salary', '')
        if salary:
            return salary

        # Try to extract from other fields
        for key in extensions:
            if 'salary' in key.lower() or '$' in str(extensions[key]):
                return str(extensions[key])

        return 'Not specified'

    def _format_salary(self, min_sal: float, max_sal: float) -> str:
        """Format salary range"""
        if min_sal and max_sal:
            return f"${int(min_sal):,} - ${int(max_sal):,}"
        elif min_sal:
            return f"${int(min_sal):,}+"
        return 'Not specified'

    def _extract_employment_type(self, job: Dict) -> str:
        """Extract employment type"""
        extensions = job.get('detected_extensions', {})
        return extensions.get('schedule_type', 'Full-time')

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description using keyword matching"""
        if not description:
            return []

        common_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust',
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git',
            'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch',
            'Machine Learning', 'Data Science', 'AI', 'TensorFlow', 'PyTorch',
            'Agile', 'Scrum', 'DevOps', 'CI/CD', 'Microservices', 'REST API'
        ]

        found_skills = []
        description_lower = description.lower()

        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)

        return found_skills[:8]  # Limit to 8 skills

    def _determine_experience_level(self, title: str) -> str:
        """Determine experience level from job title"""
        title_lower = title.lower()

        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'staff']):
            return 'Senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'intern']):
            return 'Entry'
        else:
            return 'Mid'

    def _is_remote_job(self, job: Dict) -> bool:
        """Check if job is remote-friendly"""
        location = job.get('location', '').lower()
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute', 'distributed']

        return any(keyword in location or keyword in title or keyword in description
                  for keyword in remote_keywords)

    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits from job description"""
        if not description:
            return []

        benefit_keywords = {
            'health insurance': 'Health Insurance',
            'dental': 'Dental Insurance',
            'vision': 'Vision Insurance',
            '401k': '401(k) Plan',
            'retirement': 'Retirement Plan',
            'pto': 'Paid Time Off',
            'vacation': 'Vacation Time',
            'remote': 'Remote Work',
            'flexible': 'Flexible Schedule',
            'stock': 'Stock Options',
            'equity': 'Equity Compensation',
            'bonus': 'Performance Bonus',
            'gym': 'Gym Membership',
            'wellness': 'Wellness Program'
        }

        found_benefits = []
        description_lower = description.lower()

        for keyword, benefit in benefit_keywords.items():
            if keyword in description_lower:
                found_benefits.append(benefit)

        return found_benefits[:5]  # Limit to 5 benefits

# STEP 7: AI-Powered Chat Assistant
class JobSearchChatbot:
    """AI-powered conversational job search assistant"""

    def __init__(self, search_engine: AdvancedJobSearchEngine):
        self.search_engine = search_engine
        self.conversation_history = []
        self.user_context = {}

        # Initialize AI if available
        self.ai_enabled = HAS_OPENAI and search_engine.openai_api_key
        if self.ai_enabled:
            self.ai_chat = search_engine.ai_chat

    def process_user_message(self, message: str, user_profile: UserProfile = None) -> str:
        """Process user message and generate appropriate response"""

        # Add user message to history
        self.conversation_history.append(
            ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.datetime.now()
            )
        )

        # Analyze user intent
        intent = self._analyze_intent(message)

        # Generate response based on intent
        if intent == 'job_search':
            response = self._handle_job_search(message, user_profile)
        elif intent == 'career_advice':
            response = self._handle_career_advice(message, user_profile)
        elif intent == 'resume_help':
            response = self._handle_resume_help(message)
        elif intent == 'salary_info':
            response = self._handle_salary_inquiry(message)
        elif intent == 'company_info':
            response = self._handle_company_inquiry(message)
        else:
            response = self._handle_general_chat(message)

        # Add bot response to history
        self.conversation_history.append(
            ChatMessage(
                role="bot",
                content=response,
                timestamp=datetime.datetime.now()
            )
        )

        return response

    def _analyze_intent(self, message: str) -> str:
        """Analyze user message to determine intent"""
        message_lower = message.lower()

        # Job search keywords
        if any(keyword in message_lower for keyword in [
            'find job', 'search job', 'looking for', 'job openings',
            'positions', 'vacancies', 'opportunities', 'hiring'
        ]):
            return 'job_search'

        # Career advice keywords
        if any(keyword in message_lower for keyword in [
            'career advice', 'career path', 'should i', 'career change',
            'growth', 'promotion', 'next step'
        ]):
            return 'career_advice'

        # Resume help keywords
        if any(keyword in message_lower for keyword in [
            'resume', 'cv', 'curriculum vitae', 'resume help',
            'improve resume', 'resume tips'
        ]):
            return 'resume_help'

        # Salary inquiry keywords
        if any(keyword in message_lower for keyword in [
            'salary', 'pay', 'compensation', 'how much', 'wage', 'income'
        ]):
            return 'salary_info'
            # Company inquiry keywords
        if any(keyword in message_lower for keyword in [
            'company', 'employer', 'work at', 'about company', 'company culture'
        ]):
            return 'company_info'

        return 'general_chat'

    def _handle_job_search(self, message: str, user_profile: UserProfile = None) -> str:
        """Handle job search requests"""
        # Extract job title and location from message
        job_title, location = self._extract_search_params(message)

        if not job_title:
            return ("I'd be happy to help you search for jobs! Could you please specify "
                   "what type of position you're looking for? For example: "
                   "'Find me Python developer jobs in San Francisco'")

        try:
            # Perform job search
            search_results = self.search_engine.search_google_jobs_advanced(
                query=job_title,
                location=location
            )

            if not search_results:
                return f"I couldn't find any {job_title} positions right now. Try a different job title or location."

            # Format response
            response = f"Great! I found {len(search_results)} {job_title} positions"
            if location:
                response += f" in {location}"
            response += ":\n\n"

            # Show top 3 results in chat
            for i, job in enumerate(search_results[:3], 1):
                response += f"{i}. **{job.title}** at {job.company}\n"
                response += f"   📍 {job.location}\n"
                if job.salary and job.salary != 'Not specified':
                    response += f"   💰 {job.salary}\n"
                response += f"   📅 Posted: {job.posted_date}\n\n"

            if len(search_results) > 3:
                response += f"... and {len(search_results) - 3} more positions available!\n"

            response += "\nWould you like me to show more details about any of these positions or search for something else?"

            # Store results for later use
            st.session_state['last_search_results'] = search_results

            return response

        except Exception as e:
            return f"Sorry, I encountered an error while searching for jobs: {str(e)}"

    def _handle_career_advice(self, message: str, user_profile: UserProfile = None) -> str:
        """Handle career advice requests"""
        advice_responses = {
            'career_change': [
                "Career changes can be exciting! Here are some steps to consider:",
                "• Assess your transferable skills and how they apply to your target field",
                "• Research the new industry thoroughly - trends, key players, required skills",
                "• Consider starting with side projects or volunteering in your target area",
                "• Network with professionals in your desired field",
                "• Update your resume to highlight relevant experience",
                "• Consider additional training or certifications if needed"
            ],
            'skill_development': [
                "Continuous learning is key to career growth! Here's how to approach it:",
                "• Identify in-demand skills in your field through job postings",
                "• Use platforms like Coursera, Udemy, or LinkedIn Learning",
                "• Practice with real projects - build a portfolio",
                "• Join professional communities and attend webinars",
                "• Seek mentorship from experienced professionals",
                "• Consider formal certifications for credibility"
            ],
            'promotion': [
                "Looking for a promotion? Here's a strategic approach:",
                "• Document your achievements and quantify your impact",
                "• Seek feedback from your manager regularly",
                "• Take on additional responsibilities voluntarily",
                "• Improve your visibility within the organization",
                "• Develop leadership and communication skills",
                "• Build relationships across different departments"
            ]
        }

        message_lower = message.lower()

        if 'change' in message_lower or 'switch' in message_lower:
            return '\n'.join(advice_responses['career_change'])
        elif 'skill' in message_lower or 'learn' in message_lower:
            return '\n'.join(advice_responses['skill_development'])
        elif 'promotion' in message_lower or 'advance' in message_lower:
            return '\n'.join(advice_responses['promotion'])
        else:
            return ("I'd be happy to provide career advice! Could you be more specific about what you'd like help with? "
                   "For example: career change, skill development, getting a promotion, or something else?")

    def _handle_resume_help(self, message: str) -> str:
        """Handle resume help requests"""
        resume_tips = [
            "📝 **Resume Tips for Success:**",
            "",
            "**Structure:**",
            "• Keep it to 1-2 pages maximum",
            "• Use a clean, professional format",
            "• Include: Contact info, Summary, Experience, Education, Skills",
            "",
            "**Content Tips:**",
            "• Use action verbs (achieved, implemented, led, optimized)",
            "• Quantify achievements with numbers when possible",
            "• Tailor your resume for each job application",
            "• Include relevant keywords from job descriptions",
            "",
            "**Common Mistakes to Avoid:**",
            "• Generic objective statements",
            "• Listing job duties instead of achievements",
            "• Poor formatting or typos",
            "• Including irrelevant personal information",
            "",
            "**Pro Tips:**",
            "• Use the STAR method (Situation, Task, Action, Result)",
            "• Include a compelling professional summary",
            "• Showcase your most relevant experience first",
            "• Get feedback from industry professionals"
        ]

        return '\n'.join(resume_tips)

    def _handle_salary_inquiry(self, message: str) -> str:
        """Handle salary-related questions"""
        return ("💰 **Salary Research Tips:**\n\n"
                "To get accurate salary information:\n"
                "• Check websites like Glassdoor, PayScale, and Salary.com\n"
                "• Research by location, experience level, and company size\n"
                "• Consider total compensation (base + benefits + equity)\n"
                "• Network with professionals in your field\n"
                "• Factor in cost of living for different locations\n\n"
                "What specific role or location would you like salary info for?")

    def _handle_company_inquiry(self, message: str) -> str:
        """Handle company-related questions"""
        return ("🏢 **Company Research Tips:**\n\n"
                "When researching companies:\n"
                "• Check their official website and recent news\n"
                "• Read employee reviews on Glassdoor and Indeed\n"
                "• Look at their social media and company culture\n"
                "• Review their financial performance and growth\n"
                "• Check their LinkedIn page for recent updates\n"
                "• Research their competitors and market position\n\n"
                "Which company would you like to know more about?")

    def _handle_general_chat(self, message: str) -> str:
        """Handle general conversation"""
        if self.ai_enabled:
            try:
                # Use AI for general chat
                system_message = SystemMessage(content=
                    "You are a helpful job search assistant. Provide brief, friendly responses "
                    "and try to guide the conversation back to job search topics when appropriate."
                )
                human_message = HumanMessage(content=message)

                response = self.ai_chat([system_message, human_message])
                return response.content
            except Exception as e:
                st.warning(f"AI chat error: {e}")

        # Fallback responses
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(greeting in message.lower() for greeting in greetings):
            return ("Hello! 👋 I'm your AI job search assistant. I can help you:\n"
                   "• Find job opportunities\n"
                   "• Provide career advice\n"
                   "• Help with resume tips\n"
                   "• Research salaries and companies\n\n"
                   "What would you like to explore today?")

        return ("I'm here to help with your job search! You can ask me to:\n"
               "• Search for specific jobs\n"
               "• Provide career guidance\n"
               "• Help with resume improvement\n"
               "• Give salary insights\n\n"
               "What can I help you with?")

    def _extract_search_params(self, message: str) -> Tuple[str, str]:
        """Extract job title and location from user message"""
        # Simple extraction logic - can be enhanced with NLP
        message_lower = message.lower()

        # Common job search patterns
        patterns = [
            r'find (?:me )?(.+?) (?:jobs?|positions?) (?:in|at|near) (.+)',
            r'search for (.+?) (?:jobs?|positions?) (?:in|at|near) (.+)',
            r'looking for (.+?) (?:jobs?|positions?) (?:in|at|near) (.+)',
            r'(.+?) (?:jobs?|positions?) (?:in|at|near) (.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                job_title = match.group(1).strip()
                location = match.group(2).strip()
                return job_title, location

        # Try to extract just job title
        job_patterns = [
            r'find (?:me )?(.+?) (?:jobs?|positions?)',
            r'search for (.+?) (?:jobs?|positions?)',
            r'looking for (.+?) (?:jobs?|positions?)',
        ]

        for pattern in job_patterns:
            match = re.search(pattern, message_lower)
            if match:
                job_title = match.group(1).strip()
                return job_title, ""

        return "", ""

# STEP 8: Database Management System
class JobSearchDatabase:
    """SQLite database for storing job search data"""

    def __init__(self, db_path: str = "job_search.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    salary TEXT,
                    posted_date TEXT,
                    source TEXT,
                    employment_type TEXT,
                    experience_level TEXT,
                    skills TEXT,
                    benefits TEXT,
                    remote_friendly BOOLEAN,
                    rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User searches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    location TEXT,
                    filters TEXT,
                    results_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    skills TEXT,
                    experience_level TEXT,
                    preferred_locations TEXT,
                    salary_range TEXT,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            st.error(f"Database initialization error: {e}")

    def save_jobs(self, jobs: List[JobResult]) -> int:
        """Save job results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            saved_count = 0
            for job in jobs:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO jobs
                        (job_id, title, company, location, description, url, salary,
                         posted_date, source, employment_type, experience_level,
                         skills, benefits, remote_friendly, rating)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job.job_id or f"{job.source}_{hash(job.title + job.company)}",
                        job.title, job.company, job.location, job.description, job.url,
                        job.salary, job.posted_date, job.source, job.employment_type,
                        job.experience_level, json.dumps(job.skills_required or []),
                        json.dumps(job.benefits or []), job.remote_friendly, job.rating
                    ))
                    saved_count += 1
                except Exception as e:
                    st.warning(f"Error saving job {job.title}: {e}")

            conn.commit()
            conn.close()
            return saved_count

        except Exception as e:
            st.error(f"Database save error: {e}")
            return 0

    def search_saved_jobs(self, query: str = "", location: str = "",
                         filters: Dict = None) -> List[JobResult]:
        """Search saved jobs in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query
            sql = "SELECT * FROM jobs WHERE 1=1"
            params = []

            if query:
                sql += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

            if location:
                sql += " AND location LIKE ?"
                params.append(f"%{location}%")

            if filters:
                if filters.get('employment_type'):
                    sql += " AND employment_type = ?"
                    params.append(filters['employment_type'])

                if filters.get('experience_level'):
                    sql += " AND experience_level = ?"
                    params.append(filters['experience_level'])

                if filters.get('remote_only'):
                    sql += " AND remote_friendly = 1"

            sql += " ORDER BY created_at DESC LIMIT 50"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Convert to JobResult objects
            jobs = []
            for row in rows:
                job = JobResult(
                    title=row[2], company=row[3], location=row[4],
                    description=row[5], url=row[6], salary=row[7],
                    posted_date=row[8], source=row[9], employment_type=row[10],
                    experience_level=row[11],
                    skills_required=json.loads(row[12]) if row[12] else [],
                    benefits=json.loads(row[13]) if row[13] else [],
                    remote_friendly=bool(row[14]), rating=row[15] or 0.0,
                    job_id=row[1]
                )
                jobs.append(job)

            conn.close()
            return jobs

        except Exception as e:
            st.error(f"Database search error: {e}")
            return []

    def save_search_history(self, query: str, location: str, results_count: int):
        """Save search history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO user_searches (query, location, results_count)
                VALUES (?, ?, ?)
            ''', (query, location, results_count))

            conn.commit()
            conn.close()

        except Exception as e:
            st.error(f"Error saving search history: {e}")

    def get_search_analytics(self) -> Dict:
        """Get search analytics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Most searched queries
            cursor.execute('''
                SELECT query, COUNT(*) as count
                FROM user_searches
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_queries = cursor.fetchall()

            # Search trends by date
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM user_searches
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            ''')
            daily_searches = cursor.fetchall()

            # Job sources distribution
            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM jobs
                GROUP BY source
                ORDER BY count DESC
            ''')
            job_sources = cursor.fetchall()

            conn.close()

            return {
                'top_queries': top_queries,
                'daily_searches': daily_searches,
                'job_sources': job_sources
            }

        except Exception as e:
            st.error(f"Analytics error: {e}")
            return {}

# STEP 9: Data Visualization and Analytics
class JobAnalytics:
    """Advanced job market analytics and visualization"""

    def __init__(self, database: JobSearchDatabase):
        self.db = database

    def create_salary_distribution_chart(self, jobs: List[JobResult]) -> go.Figure:
        """Create salary distribution visualization"""
        salaries = []
        job_titles = []

        for job in jobs:
            if job.salary and job.salary != 'Not specified':
                # Extract numeric values from salary strings
                salary_nums = re.findall(r'\$?(\d+(?:,\d+)*)', job.salary.replace(',', ''))
                if salary_nums:
                    # Use average if range is provided
                    if len(salary_nums) >= 2:
                        avg_salary = (int(salary_nums[0]) + int(salary_nums[1])) / 2
                    else:
                        avg_salary = int(salary_nums[0])

                    salaries.append(avg_salary)
                    job_titles.append(job.title)

        if not salaries:
            return go.Figure().add_annotation(
                text="No salary data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        fig = px.histogram(
            x=salaries,
            nbins=20,
            title="Salary Distribution",
            labels={'x': 'Salary ($)', 'y': 'Number of Jobs'}
        )

        fig.update_layout(
            showlegend=False,
            template='plotly_white',
            title_x=0.5
        )

        return fig

    def create_skills_demand_chart(self, jobs: List[JobResult]) -> go.Figure:
        """Create skills demand visualization"""
        all_skills = []

        for job in jobs:
            if job.skills_required:
                all_skills.extend(job.skills_required)

        if not all_skills:
            return go.Figure().add_annotation(
                text="No skills data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(15)

        skills, counts = zip(*top_skills)

        fig = px.bar(
            x=list(counts),
            y=list(skills),
            orientation='h',
            title="Most In-Demand Skills",
            labels={'x': 'Number of Job Postings', 'y': 'Skills'}
        )

        fig.update_layout(
            template='plotly_white',
            title_x=0.5,
            yaxis={'categoryorder': 'total ascending'}
        )

        return fig

    def create_location_distribution_chart(self, jobs: List[JobResult]) -> go.Figure:
        """Create job location distribution chart"""
        locations = [job.location for job in jobs if job.location]

        if not locations:
            return go.Figure().add_annotation(
                text="No location data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        location_counts = Counter(locations)
        top_locations = location_counts.most_common(10)

        locations, counts = zip(*top_locations)

        fig = px.pie(
            values=list(counts),
            names=list(locations),
            title="Job Distribution by Location"
        )

        fig.update_layout(
            template='plotly_white',
            title_x=0.5
        )

        return fig

    def create_company_analysis_chart(self, jobs: List[JobResult]) -> go.Figure:
        """Create company hiring analysis"""
        companies = [job.company for job in jobs if job.company]

        if not companies:
            return go.Figure().add_annotation(
                text="No company data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        company_counts = Counter(companies)
        top_companies = company_counts.most_common(10)

        companies, counts = zip(*top_companies)

        fig = px.bar(
            x=list(companies),
            y=list(counts),
            title="Top Hiring Companies",
            labels={'x': 'Company', 'y': 'Number of Open Positions'}
        )

        fig.update_layout(
            template='plotly_white',
            title_x=0.5,
            xaxis_tickangle=-45
        )

        return fig

    def create_experience_level_chart(self, jobs: List[JobResult]) -> go.Figure:
        """Create experience level distribution chart"""
        experience_levels = [job.experience_level for job in jobs if job.experience_level]

        if not experience_levels:
            return go.Figure().add_annotation(
                text="No experience level data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        exp_counts = Counter(experience_levels)

        fig = px.bar(
            x=list(exp_counts.keys()),
            y=list(exp_counts.values()),
            title="Job Distribution by Experience Level",
            labels={'x': 'Experience Level', 'y': 'Number of Jobs'},
            color=list(exp_counts.values()),
            color_continuous_scale='viridis'
        )

        fig.update_layout(
            template='plotly_white',
            title_x=0.5,
            showlegend=False
        )

        return fig

# STEP 10: Main Streamlit Application
def main():
    """Main application function"""

    # Initialize session state
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = AdvancedJobSearchEngine()

    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = JobSearchChatbot(st.session_state.search_engine)

    if 'database' not in st.session_state:
        st.session_state.database = JobSearchDatabase()

    if 'analytics' not in st.session_state:
        st.session_state.analytics = JobAnalytics(st.session_state.database)

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'current_jobs' not in st.session_state:
        st.session_state.current_jobs = []

    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = UserProfile()

    # Main header
    st.markdown("""
        <div class="main-header">
            <h1>🤖 AI Job Search Assistant</h1>
            <p>Your intelligent companion for finding the perfect job opportunity</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.selectbox(
            "Choose a feature:",
            ["💬 Chat Assistant", "🔍 Advanced Search", "📊 Analytics", "👤 Profile", "💾 Saved Jobs"]
        )

        st.markdown("---")

        # Quick search in sidebar
        st.header("⚡ Quick Search")
        quick_job = st.text_input("Job Title", placeholder="e.g., Python Developer")
        quick_location = st.text_input("Location", placeholder="e.g., San Francisco, CA")

        if st.button("🚀 Quick Search", use_container_width=True):
            if quick_job:
                with st.spinner("Searching for jobs..."):
                    results = st.session_state.search_engine.search_google_jobs_advanced(
                        query=quick_job,
                        location=quick_location
                    )
                    st.session_state.current_jobs = results
                    st.session_state.database.save_jobs(results)
                    st.rerun()

        st.markdown("---")

        # Settings
        st.header("⚙️ Settings")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("🔄 Reset All Data"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Main content based on selected page
    if page == "💬 Chat Assistant":
        show_chat_interface()
    elif page == "🔍 Advanced Search":
        show_advanced_search()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "👤 Profile":
        show_profile_page()
    elif page == "💾 Saved Jobs":
        show_saved_jobs()

def show_chat_interface():
    """Display chat interface"""
    st.header("💬 AI Chat Assistant")

    # Chat history display
    chat_container = st.container()

    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
                if message.role == "user":
                    st.markdown(f"""
                        <div class="user-message">
                            <strong>You:</strong> {message.content}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="bot-message">
                            <strong>Assistant:</strong> {message.content}
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👋 Welcome! I'm your AI job search assistant. Ask me anything about finding jobs, career advice, or resume tips!")

    # Chat input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Process user message
        response = st.session_state.chatbot.process_user_message(
            user_input,
            st.session_state.user_profile
        )

        # Add to session state
        st.session_state.chat_history.extend([
            ChatMessage(role="user", content=user_input, timestamp=datetime.datetime.now()),
            ChatMessage(role="bot", content=response, timestamp=datetime.datetime.now())
        ])

        st.rerun()

    # Display current job results if any
    if st.session_state.current_jobs:
        st.markdown("### 📋 Current Job Results")
        display_job_results(st.session_state.current_jobs)

def show_advanced_search():
    """Display advanced search interface"""
    st.header("🔍 Advanced Job Search")

    col1, col2 = st.columns(2)

    with col1:
        job_title = st.text_input("🎯 Job Title *", placeholder="e.g., Software Engineer")
        location = st.text_input("📍 Location", placeholder="e.g., New York, NY")

        employment_type = st.selectbox(
            "💼 Employment Type",
            ["Any", "Full-time", "Part-time", "Contract", "Internship"]
        )
        experience_level = st.selectbox(
            "🎓 Experience Level",
            ["Any", "Entry", "Mid", "Senior", "Executive"]
        )

        salary_range = st.select_slider(
            "💰 Salary Range (K)",
            options=[30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200],
            value=(50, 120),
            format_func=lambda x: f"${x}K"
        )

        remote_only = st.checkbox("🏠 Remote Jobs Only")

    # Advanced filters
    with st.expander("🔧 Advanced Filters"):
        col3, col4 = st.columns(2)

        with col3:
            company_size = st.selectbox(
                "🏢 Company Size",
                ["Any", "Startup (1-50)", "Mid-size (51-500)", "Large (500+)"]
            )

            industry = st.selectbox(
                "🏭 Industry",
                ["Any", "Technology", "Healthcare", "Finance", "Education",
                 "Manufacturing", "Retail", "Consulting", "Government"]
            )

        with col4:
            posted_date = st.selectbox(
                "📅 Posted Date",
                ["Any time", "Past 24 hours", "Past week", "Past month"]
            )

            job_function = st.selectbox(
                "⚙️ Job Function",
                ["Any", "Engineering", "Sales", "Marketing", "Operations",
                 "Finance", "HR", "Design", "Customer Service"]
            )

    # Search button
    if st.button("🔍 Search Jobs", type="primary", use_container_width=True):
        if not job_title:
            st.error("Please enter a job title to search!")
            return

        # Build search filters
        filters = {
            'employment_type': employment_type if employment_type != "Any" else None,
            'experience_level': experience_level if experience_level != "Any" else None,
            'salary_min': salary_range[0] * 1000,
            'salary_max': salary_range[1] * 1000,
            'remote_only': remote_only,
            'company_size': company_size if company_size != "Any" else None,
            'industry': industry if industry != "Any" else None,
            'posted_date': posted_date if posted_date != "Any time" else None,
            'job_function': job_function if job_function != "Any" else None
        }

        with st.spinner("🔍 Searching for jobs... This may take a moment."):
            try:
                # Perform search
                results = st.session_state.search_engine.search_google_jobs_advanced(
                    query=job_title,
                    location=location,
                    filters=filters
                )

                if results:
                    st.session_state.current_jobs = results
                    st.session_state.database.save_jobs(results)
                    st.session_state.database.save_search_history(
                        job_title, location or "Any", len(results)
                    )
                    st.success(f"✅ Found {len(results)} job opportunities!")
                else:
                    st.warning("No jobs found matching your criteria. Try adjusting your search parameters.")

            except Exception as e:
                st.error(f"Search error: {str(e)}")

    # Display results
    if st.session_state.current_jobs:
        st.markdown("---")
        display_job_results(st.session_state.current_jobs)

def show_analytics():
    """Display analytics and insights"""
    st.header("📊 Job Market Analytics")

    # Get current jobs for analysis
    jobs = st.session_state.current_jobs

    if not jobs:
        st.info("🔍 Search for jobs first to see analytics!")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📈 Total Jobs Found", len(jobs))

    with col2:
        remote_jobs = sum(1 for job in jobs if job.remote_friendly)
        st.metric("🏠 Remote Jobs", remote_jobs, f"{remote_jobs/len(jobs)*100:.1f}%")

    with col3:
        companies = len(set(job.company for job in jobs if job.company))
        st.metric("🏢 Unique Companies", companies)

    with col4:
        avg_rating = sum(job.rating for job in jobs if job.rating) / len([j for j in jobs if j.rating])
        st.metric("⭐ Avg Company Rating", f"{avg_rating:.1f}" if avg_rating else "N/A")

    # Charts
    st.markdown("---")

    # Salary distribution
    col1, col2 = st.columns(2)

    with col1:
        salary_chart = st.session_state.analytics.create_salary_distribution_chart(jobs)
        st.plotly_chart(salary_chart, use_container_width=True)

    with col2:
        location_chart = st.session_state.analytics.create_location_distribution_chart(jobs)
        st.plotly_chart(location_chart, use_container_width=True)

    # Skills and companies
    col3, col4 = st.columns(2)

    with col3:
        skills_chart = st.session_state.analytics.create_skills_demand_chart(jobs)
        st.plotly_chart(skills_chart, use_container_width=True)

    with col4:
        company_chart = st.session_state.analytics.create_company_analysis_chart(jobs)
        st.plotly_chart(company_chart, use_container_width=True)

    # Experience level distribution
    exp_chart = st.session_state.analytics.create_experience_level_chart(jobs)
    st.plotly_chart(exp_chart, use_container_width=True)

    # Search analytics
    st.markdown("---")
    st.subheader("🔍 Search Analytics")

    analytics_data = st.session_state.database.get_search_analytics()

    if analytics_data.get('top_queries'):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Most Searched Terms:**")
            for query, count in analytics_data['top_queries'][:5]:
                st.write(f"• {query}: {count} searches")

        with col2:
            st.markdown("**Job Sources:**")
            for source, count in analytics_data.get('job_sources', [])[:5]:
                st.write(f"• {source}: {count} jobs")

def show_profile_page():
    """Display user profile management"""
    st.header("👤 User Profile")

    profile = st.session_state.user_profile

    with st.form("profile_form"):
        st.subheader("📝 Personal Information")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name", value=profile.name or "")
            email = st.text_input("Email", value=profile.email or "")
            phone = st.text_input("Phone", value=profile.phone or "")

        with col2:
            experience_level = st.selectbox(
                "Experience Level",
                ["Entry", "Mid", "Senior", "Executive"],
                index=["Entry", "Mid", "Senior", "Executive"].index(profile.experience_level)
                if profile.experience_level in ["Entry", "Mid", "Senior", "Executive"] else 0
            )

            current_location = st.text_input("Current Location", value=profile.current_location or "")
            linkedin_url = st.text_input("LinkedIn URL", value=profile.linkedin_url or "")

        st.subheader("💼 Professional Details")

        skills = st.text_area(
            "Skills (comma-separated)",
            value=", ".join(profile.skills) if profile.skills else "",
            help="e.g., Python, JavaScript, Project Management, SQL"
        )

        preferred_locations = st.text_area(
            "Preferred Job Locations (comma-separated)",
            value=", ".join(profile.preferred_locations) if profile.preferred_locations else "",
            help="e.g., New York, San Francisco, Remote"
        )

        col3, col4 = st.columns(2)

        with col3:
            desired_salary_min = st.number_input("Desired Salary Min ($)", value=profile.desired_salary_min or 50000, step=5000)
            desired_salary_max = st.number_input("Desired Salary Max ($)", value=profile.desired_salary_max or 100000, step=5000)

        with col4:
            job_types = st.multiselect(
                "Preferred Job Types",
                ["Full-time", "Part-time", "Contract", "Internship"],
                default=profile.job_types or ["Full-time"]
            )

            remote_preference = st.selectbox(
                "Remote Work Preference",
                ["No preference", "Remote only", "Hybrid", "On-site only"],
                index=["No preference", "Remote only", "Hybrid", "On-site only"].index(profile.remote_preference)
                if profile.remote_preference in ["No preference", "Remote only", "Hybrid", "On-site only"] else 0
            )

        st.subheader("🎯 Career Goals")
        career_goals = st.text_area(
            "Career Goals & Interests",
            value=profile.career_goals or "",
            help="Describe your career aspirations and interests"
        )

        if st.form_submit_button("💾 Save Profile", type="primary"):
            # Update profile
            profile.name = name
            profile.email = email
            profile.phone = phone
            profile.experience_level = experience_level
            profile.current_location = current_location
            profile.linkedin_url = linkedin_url
            profile.skills = [skill.strip() for skill in skills.split(",") if skill.strip()]
            profile.preferred_locations = [loc.strip() for loc in preferred_locations.split(",") if loc.strip()]
            profile.desired_salary_min = desired_salary_min
            profile.desired_salary_max = desired_salary_max
            profile.job_types = job_types
            profile.remote_preference = remote_preference
            profile.career_goals = career_goals

            st.success("✅ Profile saved successfully!")
            st.rerun()

    # Profile summary
    if profile.name:
        st.markdown("---")
        st.subheader("📋 Profile Summary")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Name:** {profile.name}")
            st.write(f"**Experience:** {profile.experience_level}")
            st.write(f"**Location:** {profile.current_location or 'Not specified'}")
            st.write(f"**Skills:** {len(profile.skills)} skills listed")

        with col2:
            st.write(f"**Salary Range:** ${profile.desired_salary_min:,} - ${profile.desired_salary_max:,}")
            st.write(f"**Job Types:** {', '.join(profile.job_types)}")
            st.write(f"**Remote Preference:** {profile.remote_preference}")
            st.write(f"**Target Locations:** {len(profile.preferred_locations)} locations")

def show_saved_jobs():
    """Display saved jobs interface"""
    st.header("💾 Saved Jobs")

    # Search saved jobs
    col1, col2, col3 = st.columns(3)

    with col1:
        search_query = st.text_input("🔍 Search saved jobs", placeholder="Job title or company")

    with col2:
        search_location = st.text_input("📍 Location filter", placeholder="Location")

    with col3:
        employment_filter = st.selectbox("💼 Employment Type", ["All", "Full-time", "Part-time", "Contract"])

    # Get saved jobs
    filters = {}
    if employment_filter != "All":
        filters['employment_type'] = employment_filter

    saved_jobs = st.session_state.database.search_saved_jobs(
        query=search_query,
        location=search_location,
        filters=filters
    )

    if saved_jobs:
        st.write(f"Found {len(saved_jobs)} saved jobs")
        display_job_results(saved_jobs)
    else:
        st.info("No saved jobs found. Start searching to save jobs!")

        if st.button("🔍 Go to Search"):
            st.switch_page("🔍 Advanced Search")

def display_job_results(jobs: List[JobResult]):
    """Display job results in a formatted way"""

    # Add sorting options
    col1, col2, col3 = st.columns(3)

    with col1:
        sort_by = st.selectbox("Sort by:", ["Relevance", "Date", "Salary", "Company"])

    with col2:
        jobs_per_page = st.selectbox("Jobs per page:", [10, 20, 50], index=1)

    with col3:
        show_details = st.checkbox("Show full details", value=False)

    # Sort jobs
    if sort_by == "Date":
        jobs = sorted(jobs, key=lambda x: x.posted_date or "", reverse=True)
    elif sort_by == "Salary":
        jobs = sorted(jobs, key=lambda x: extract_salary_number(x.salary), reverse=True)
    elif sort_by == "Company":
        jobs = sorted(jobs, key=lambda x: x.company or "")

    # Pagination
    total_pages = (len(jobs) - 1) // jobs_per_page + 1

    if total_pages > 1:
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        start_idx = (page - 1) * jobs_per_page
        end_idx = start_idx + jobs_per_page
        displayed_jobs = jobs[start_idx:end_idx]
    else:
        displayed_jobs = jobs[:jobs_per_page]

    # Display jobs
    for i, job in enumerate(displayed_jobs):
        with st.container():
            # Job header
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### 🎯 {job.title}")
                st.markdown(f"**🏢 {job.company}** | 📍 {job.location}")

                # Job details in chips
                details = []
                if job.employment_type:
                    details.append(f"💼 {job.employment_type}")
                if job.experience_level:
                    details.append(f"🎓 {job.experience_level}")
                if job.salary and job.salary != 'Not specified':
                    details.append(f"💰 {job.salary}")
                if job.remote_friendly:
                    details.append("🏠 Remote Friendly")

                if details:
                    st.markdown(" | ".join(details))

            with col2:
                st.markdown(f"**📅 Posted:** {job.posted_date}")
                if job.rating:
                    st.markdown(f"**⭐ Rating:** {job.rating}/5.0")

                if job.url:
                    st.markdown(f"[🔗 Apply Now]({job.url})")

            # Job description
            if show_details and job.description:
                with st.expander("📋 Job Description"):
                    st.write(job.description[:500] + "..." if len(job.description) > 500 else job.description)

            # Skills and benefits
            if show_details:
                col3, col4 = st.columns(2)

                with col3:
                    if job.skills_required:
                        st.markdown("**🔧 Required Skills:**")
                        skills_text = ", ".join(job.skills_required[:10])  # Show first 10 skills
                        st.write(skills_text)

                with col4:
                    if job.benefits:
                        st.markdown("**🎁 Benefits:**")
                        benefits_text = ", ".join(job.benefits[:5])  # Show first 5 benefits
                        st.write(benefits_text)

            st.markdown("---")

def extract_salary_number(salary_str: str) -> int:
    """Extract numeric value from salary string for sorting"""
    if not salary_str or salary_str == 'Not specified':
        return 0

    # Extract numbers from salary string
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return int(numbers[0])
    return 0

# CSS Styling
def load_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #2196f3;
    }

    .bot-message {
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #4caf50;
    }

    .job-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        background-color: #fafafa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .job-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-1px);
        transition: all 0.2s ease;
    }

    .sidebar .stSelectbox label {
        font-weight: bold;
        color: #333;
    }

    .stAlert {
        border-radius: 10px;
    }

    .stSuccess {
        background-color: #d4edda;
        border-color: #c3e6cb;
    }

    .stError {
        background-color: #f8d7da;
        border-color: #f5c6cb;
    }

    .stInfo {
        background-color: #cce7ff;
        border-color: #b8daff;
    }

    .stWarning {
        background-color: #fff3cd;
        border-color: #ffeaa7;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize and run the application
if __name__ == "__main__":
    st.set_page_config(
        page_title="AI Job Search Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load custom CSS
    load_css()

    # Run main application
    main()

# ADDITIONAL UTILITY FUNCTIONS

def export_jobs_to_csv(jobs: List[JobResult]) -> str:
    """Export jobs to CSV format"""
    if not jobs:
        return ""

    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Title', 'Company', 'Location', 'Salary', 'Posted Date',
        'Employment Type', 'Experience Level', 'URL', 'Description'
    ])

    # Write job data
    for job in jobs:
        writer.writerow([
            job.title, job.company, job.location, job.salary,
            job.posted_date, job.employment_type, job.experience_level,
            job.url, job.description[:200] + "..." if len(job.description or "") > 200 else job.description
        ])

    return output.getvalue()

def send_job_alert_email(email: str, jobs: List[JobResult], query: str):
    """Send job alert email (placeholder for email integration)"""
    # This would integrate with email service like SendGrid, AWS SES, etc.
    # For now, we'll just log the alert
    print(f"Job alert for {email}: Found {len(jobs)} jobs for '{query}'")

def schedule_job_alerts():
    """Schedule regular job alerts (placeholder for scheduler integration)"""
    # This would integrate with task scheduler like Celery, APScheduler, etc.
    # For now, we'll just log the scheduling
    print("Job alerts scheduled")

# ERROR HANDLING AND LOGGING
import logging

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('job_search_app.log'),
            logging.StreamHandler()
        ]
    )
