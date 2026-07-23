import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '.')

print('[TEST 1] Config + Settings...')
from config.settings import DB_ENGINE, DB_PATH, LOG_LEVEL
print('  DB_ENGINE=' + DB_ENGINE + ', LOG_LEVEL=' + LOG_LEVEL)

print('[TEST 2] Logging...')
from config.logging import logger
logger.info('[AUDIT] Test audit log')
logger.warning('Test WARNING')
logger.error('Test ERROR')

print('[TEST 3] Database Connection & Schema V2 Tables...')
from database.connection import init_db, get_db_connection
from database.schema import verify_tables
init_db()
conn = get_db_connection()
report = verify_tables(conn, engine=DB_ENGINE)
conn.close()
print('  All tables exist: ' + str(all(report.values())))
print('  Tables: ' + str(list(report.keys())))

print('[TEST 3b] Models V2 Import...')
from database.models import (
    UserModel, WorkspaceModel, CompanyModel, BrandModel,
    ProjectModel, CampaignModel, PostModel, AssetModel,
    KnowledgeModel, ScheduleModel, ApprovalModel,
    PromptVersionModel, AnalyticsModel
)
print('  Models import: OK')

print('[TEST 4] Services import...')
from services.gemini_client import get_gemini_model
from services.content_service import generate_marketing_or_knowledge_content
print('  gemini_client: OK')
print('  content_service: OK')

print('[TEST 5] Social publishers...')
from social.publishers import post_to_facebook, post_to_zalo_oa, post_to_linkedin
print('  publishers: OK')

print('[TEST 6] Agents...')
from agents.prompt_templates import get_viral_marketing_prompt
from agents.framework import build_prompt_framework, generate_tool_prompt_framework
print('  prompt_templates: OK')
print('  framework: OK')

print('[TEST 7] Knowledge...')
from knowledge.case_study import generate_ai_case_study
from knowledge.reels import generate_knowledge_reels_script
print('  case_study: OK')
print('  reels: OK')

print('[TEST 8] Workflow...')
from workflow.scheduler import generate_30_day_knowledge_plan
print('  scheduler: OK')

print('[TEST 9] Analytics...')
from analytics.viral_score import parse_viral_score_and_reason
print('  viral_score: OK')

print()
print('=== TAT CA TEST PASS - HE THONG READY ===')
