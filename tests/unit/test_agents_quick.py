from agent.treatment import treatment
from agent.remediator import remediator

print('✅ Treatment agent loaded')
print('✅ Remediator agent loaded')

issue = {'issue_type': 'missing_dob', 'CUS_ID': 'C001'}
result = treatment.analyze_and_suggest(issue)
print(f'✅ Root causes: {len(result["root_causes"])}')
print(f'✅ Treatments: {len(result["treatments"])}')
print(f'✅ Top treatment: {result["treatments"][0]["description"][:50]}...')

