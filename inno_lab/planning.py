import datetime

from .constants import PLAN_TEMPLATE, TRIAL
from .models import PlanStep


def trial_text(line: str) -> str:
    return TRIAL.get(line, 'Próba technologiczna na linii docelowej')


def build_plan_steps(plan, use_template=True):
    """Create the PlanStep rows for a freshly-created TransferPlan.

    use_template=False creates zero steps ("Pusty — dodam kroki sam" in the
    original UI) so the user builds the schedule from scratch.
    """
    if not use_template:
        return []

    product_name = plan.product.name
    flavour = plan.flavour or product_name
    steps = []
    for nr, title, role, task_template in PLAN_TEMPLATE:
        if nr == 6:
            tasks = trial_text(plan.line)
        else:
            tasks = task_template.format(flavour=flavour, line=plan.line, product=product_name)
        steps.append(PlanStep(plan=plan, nr=nr, title=title, role=role, tasks=tasks, initials=''))
    PlanStep.objects.bulk_create(steps)

    if plan.start_date:
        spread_dates(plan)
    return steps


def spread_dates(plan):
    """Assign each step a date one week after the previous one, starting at
    plan.start_date."""
    if not plan.start_date:
        return
    steps = list(plan.steps.order_by('nr'))
    for i, step in enumerate(steps):
        step.date = plan.start_date + datetime.timedelta(days=7 * i)
    PlanStep.objects.bulk_update(steps, ['date'])


def switch_line(plan, new_line):
    """Change a plan's target line. If step 6's task text still matches the
    old line's canned trial description verbatim (i.e. nobody hand-edited
    it), swap in the new line's trial description too."""
    old_line = plan.line
    if old_line == new_line:
        return False
    try:
        step6 = plan.steps.get(nr=6)
        if step6.tasks == trial_text(old_line):
            step6.tasks = trial_text(new_line)
            step6.save(update_fields=['tasks'])
    except PlanStep.DoesNotExist:
        pass
    plan.line = new_line
    plan.save(update_fields=['line', 'updated_at'])
    return True


def renumber(plan):
    for i, step in enumerate(plan.steps.order_by('nr'), start=1):
        if step.nr != i:
            step.nr = i
            step.save(update_fields=['nr'])
