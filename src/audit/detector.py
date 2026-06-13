"""Audit detection rules for tender/bid document analysis."""
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from ..utils.datamodel import DocumentMeta, AuditAlert
from ..utils.datetime_util import as_naive


def _company_for(meta: DocumentMeta) -> str:
    """Return the effective company name for a document."""
    return (meta.company or '').strip() or '未知公司'


def _severity_for_company_count(count: int) -> str:
    """Map cross-company count to severity."""
    if count >= 3:
        return 'high'
    if count == 2:
        return 'medium'
    return 'low'


def check_author_consistency(results: List[DocumentMeta]) -> List[AuditAlert]:
    """Detect authors or last-modified-by users appearing across multiple companies."""
    alerts = []
    author_companies = defaultdict(set)
    modifier_companies = defaultdict(set)
    author_files = defaultdict(list)
    modifier_files = defaultdict(list)

    for meta in results:
        company = _company_for(meta)
        author = (meta.author or '').strip()
        modifier = (meta.last_modified_by or '').strip()

        if author:
            author_companies[author].add(company)
            author_files[author].append(meta.filepath)
        if modifier:
            modifier_companies[modifier].add(company)
            modifier_files[modifier].append(meta.filepath)

    for author, companies in author_companies.items():
        if len(companies) >= 2:
            alerts.append(AuditAlert(
                rule_name='author_consistency',
                severity=_severity_for_company_count(len(companies)),
                description=f'作者 "{author}" 出现在 {len(companies)} 家公司中',
                affected_companies=sorted(companies),
                affected_files=author_files[author],
                details={
                    'author': author,
                    'company_count': len(companies),
                    'file_count': len(author_files[author]),
                    'field': 'author'
                }
            ))

    for modifier, companies in modifier_companies.items():
        if len(companies) >= 2:
            alerts.append(AuditAlert(
                rule_name='author_consistency',
                severity=_severity_for_company_count(len(companies)),
                description=f'最后修改者 "{modifier}" 出现在 {len(companies)} 家公司中',
                affected_companies=sorted(companies),
                affected_files=modifier_files[modifier],
                details={
                    'modifier': modifier,
                    'company_count': len(companies),
                    'file_count': len(modifier_files[modifier]),
                    'field': 'last_modified_by'
                }
            ))

    return alerts


def _time_bucket(dt: datetime, threshold_minutes: int) -> str:
    """Round a datetime down to the nearest threshold bucket."""
    minutes = dt.hour * 60 + dt.minute
    bucket = (minutes // threshold_minutes) * threshold_minutes
    hour = bucket // 60
    minute = bucket % 60
    return dt.strftime('%Y-%m-%d') + f' {hour:02d}:{minute:02d}'


def _check_time_clustering(results: List[DocumentMeta],
                           threshold_minutes: int,
                           field: str) -> List[AuditAlert]:
    """Generic time clustering detector for created or modified fields."""
    alerts = []
    bucket_data = defaultdict(lambda: {'companies': set(), 'files': []})

    for meta in results:
        dt: Optional[datetime] = getattr(meta, field, None)
        if not isinstance(dt, datetime):
            continue
        dt = as_naive(dt)
        company = _company_for(meta)
        bucket = _time_bucket(dt, threshold_minutes)
        bucket_data[bucket]['companies'].add(company)
        bucket_data[bucket]['files'].append(meta.filepath)

    for bucket, data in bucket_data.items():
        companies = data['companies']
        if len(companies) >= 2:
            alerts.append(AuditAlert(
                rule_name=f'{field}_time_clustering',
                severity=_severity_for_company_count(len(companies)),
                description=f'{bucket} 时间段内 {len(companies)} 家公司有文件{"创建" if field == "created" else "修改"}',
                affected_companies=sorted(companies),
                affected_files=data['files'],
                details={
                    'time_bucket': bucket,
                    'threshold_minutes': threshold_minutes,
                    'company_count': len(companies),
                    'file_count': len(data['files']),
                    'field': field
                }
            ))

    return alerts


def check_creation_time_clustering(results: List[DocumentMeta],
                                   threshold_minutes: int = 30) -> List[AuditAlert]:
    """Detect creation time concentration across companies."""
    return _check_time_clustering(results, threshold_minutes, 'created')


def check_modified_time_clustering(results: List[DocumentMeta],
                                   threshold_minutes: int = 30) -> List[AuditAlert]:
    """Detect modification time concentration across companies."""
    return _check_time_clustering(results, threshold_minutes, 'modified')


def check_template_reuse(results: List[DocumentMeta],
                         current_project_name: str = '') -> List[AuditAlert]:
    """Detect the same template being reused across multiple companies."""
    alerts = []
    template_companies = defaultdict(set)
    template_files = defaultdict(list)

    project_name = (current_project_name or '').strip().lower()

    for meta in results:
        template = (meta.template or '').strip()
        if not template:
            continue
        company = _company_for(meta)
        template_companies[template].add(company)
        template_files[template].append(meta.filepath)

    for template, companies in template_companies.items():
        if len(companies) >= 2:
            severity = _severity_for_company_count(len(companies))
            if project_name and project_name in template.lower():
                # Downgrade by one level if template belongs to current project
                severity = {'high': 'medium', 'medium': 'low', 'low': 'low'}.get(severity, 'low')

            alerts.append(AuditAlert(
                rule_name='template_reuse',
                severity=severity,
                description=f'模板 "{template}" 被 {len(companies)} 家公司共用',
                affected_companies=sorted(companies),
                affected_files=template_files[template],
                details={
                    'template': template,
                    'company_count': len(companies),
                    'file_count': len(template_files[template])
                }
            ))

    return alerts
