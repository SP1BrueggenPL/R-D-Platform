import csv
import datetime
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import planning
from .constants import CRIT, KATS, LINES, NOPE, NUTRI, PTYPES, ROLES
from .forms import NewPlanForm, NewStepForm, PlanEditForm, PlanStepForm, ProductFilterForm, ProductForm
from .models import PlanStep, Product, ProductPhoto, TransferPlan
from .services import ai as ai_service

PHOTO_LIMIT = 6


# --------------------------------------------------------------------------
# Scan / edit product
# --------------------------------------------------------------------------

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.source = Product.SOURCE_SESJA
            product.date = timezone.localdate()
            product.created_by = request.user
            product.save()
            _attach_uploaded_photos(product, request.FILES.getlist('photos'))
            messages.success(request, 'Zapisano ocenę w bazie.')
            return redirect('inno_lab:product_edit', pk=product.pk)
        messages.error(request, 'Wpisz nazwę produktu i uzupełnij wymagane pola przed zapisem.')
    else:
        form = ProductForm()
    return render(request, 'inno_lab/scan.html', {
        'form': form, 'product': None, 'crit': CRIT, 'photo_limit': PHOTO_LIMIT,
        'ai_enabled': settings.AI_FEATURES_ENABLED, 'ptypes': PTYPES,
    })


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            _attach_uploaded_photos(product, request.FILES.getlist('photos'))
            messages.success(request, 'Zmiany zapisane.')
            return redirect('inno_lab:product_edit', pk=product.pk)
        messages.error(request, 'Sprawdź formularz — coś jest niepoprawne.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inno_lab/scan.html', {
        'form': form, 'product': product, 'crit': CRIT, 'photo_limit': PHOTO_LIMIT,
        'ai_enabled': settings.AI_FEATURES_ENABLED, 'ptypes': PTYPES,
    })


def _attach_uploaded_photos(product, files):
    if not files:
        return
    current = list(product.photos.all())
    free = PHOTO_LIMIT - len(current)
    if free <= 0:
        return
    for i, f in enumerate(files[:free]):
        type_index = min(len(current) + i, len(PTYPES) - 1)
        ProductPhoto.objects.create(
            product=product, image=f, photo_type=PTYPES[type_index],
            original_filename=getattr(f, 'name', ''), sort_order=len(current) + i,
        )


@login_required
def photo_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        _attach_uploaded_photos(product, request.FILES.getlist('photos'))
    return redirect('inno_lab:product_edit', pk=product.pk)


@login_required
def photo_set_type(request, pk):
    photo = get_object_or_404(ProductPhoto, pk=pk)
    if request.method == 'POST' and request.POST.get('photo_type') in PTYPES:
        photo.photo_type = request.POST['photo_type']
        photo.save(update_fields=['photo_type'])
    return redirect('inno_lab:product_edit', pk=photo.product_id)


@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(ProductPhoto, pk=pk)
    product_id = photo.product_id
    if request.method == 'POST':
        photo.delete()
    return redirect('inno_lab:product_edit', pk=product_id)


@login_required
def ai_read_label(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            data = ai_service.read_label(list(product.photos.all()))
        except ai_service.AIUnavailable as exc:
            messages.error(request, f'Odczyt AI niedostępny: {exc}')
        else:
            mapping = {
                'nazwa': 'name', 'marka': 'brand', 'sklad': 'composition', 'alergeny': 'allergens',
                'claims': 'claims', 'nowe': 'whats_new', 'wyglad': 'appearance',
            }
            for src, dest in mapping.items():
                if data.get(src):
                    setattr(product, dest, data[src])
            if data.get('kat'):
                product.category = data['kat']
            for key, val in (data.get('nutri') or {}).items():
                setattr(product, key, val)
            product.save()
            messages.success(request, 'Odczyt gotowy. Sprawdź i popraw pola — dane pochodzą z AI i mogą być niepełne.')
    return redirect('inno_lab:product_edit', pk=product.pk)


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST' and product.is_deletable:
        product.delete()
        messages.success(request, 'Ocena usunięta.')
    return redirect('inno_lab:base')


# --------------------------------------------------------------------------
# Baza (list/filter/search) + export/import
# --------------------------------------------------------------------------

def _filtered_products(request):
    form = ProductFilterForm(request.GET or None)
    qs = Product.objects.all()
    if form.is_valid():
        q = form.cleaned_data.get('q') or ''
        kat = form.cleaned_data.get('kat') or 'Wszystkie'
        decf = form.cleaned_data.get('decf') or 'Wszystkie'
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(conclusion__icontains=q) | Q(whats_new__icontains=q))
        if kat and kat != 'Wszystkie':
            qs = qs.filter(category=kat)
        if decf == 'Bez decyzji':
            qs = qs.filter(target_lines=[])
        elif decf == NOPE:
            qs = qs.filter(target_lines=[NOPE])
        elif decf == 'Wybrana linia':
            qs = qs.exclude(target_lines=[]).exclude(target_lines=[NOPE])
    return form, qs.order_by('-overall_score', '-created_at')


@login_required
def base_list(request):
    form, products = _filtered_products(request)
    return render(request, 'inno_lab/base.html', {
        'form': form, 'products': products, 'count': products.count(), 'nope': NOPE,
    })


@login_required
def export_csv(request):
    _, products = _filtered_products(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inno_session_export.csv"'
    response.write('﻿')
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(['Nr', 'Data', 'Nazwa', 'Kategoria', 'Indeks 1-5', 'Co nowe', 'Wygląd',
                      'Wniosek / insight', 'Decyzja transferu', 'Postęp projektu', 'Liczba zdjęć', 'Źródło'])
    for i, p in enumerate(products, start=1):
        if p.target_lines == [NOPE]:
            postep = 'bez transferu'
        elif not p.has_plan:
            postep = 'brak planu'
        else:
            postep = f'{p.plan.progress}%'
        writer.writerow([
            i, p.date or '', p.name, p.category, p.overall_score or '', p.whats_new,
            p.appearance, p.conclusion, ' / '.join(p.target_lines) or 'brak decyzji',
            postep, p.photos.count(), p.source,
        ])
    for plan in TransferPlan.objects.all():
        for step in plan.steps.all():
            writer.writerow([
                'PLAN', plan.created_at.date(), f'{plan.product.name} -> {plan.line}',
                f'Krok {step.nr} · {step.date or ""}', '', step.title, '',
                f"{step.tasks} | {step.role} {step.initials or '?'}", plan.line,
                f'{plan.progress}%' + (' · krok zrobiony' if step.done else ''), '', 'action plan',
            ])
    return response


def _product_to_dict(p):
    return {
        'id': p.pk, 'data': str(p.date or ''), 'nazwa': p.name, 'marka': p.brand,
        'kat': p.category, 'sklad': p.composition, 'alergeny': p.allergens, 'claims': p.claims,
        'nowe': p.whats_new, 'wyglad': p.appearance, 'komentarz': p.conclusion,
        'nutri': {k: getattr(p, k) for k, _l, _u in NUTRI},
        'scores': {k: getattr(p, k) for k, _l, _w in CRIT},
        'ocena': str(p.overall_score) if p.overall_score is not None else None,
        'targets': p.target_lines, 'source': p.source,
    }


@login_required
def export_json(request):
    products = [_product_to_dict(p) for p in Product.objects.all()]
    plans = []
    for plan in TransferPlan.objects.select_related('product').all():
        plans.append({
            'product': plan.product.name, 'line': plan.line, 'flavour': plan.flavour,
            'start': str(plan.start_date or ''), 'progress': plan.progress,
            'weeks': [{'nr': s.nr, 'title': s.title, 'role': s.role, 'tasks': s.tasks,
                       'initials': s.initials, 'done': s.done, 'date': str(s.date or '')}
                      for s in plan.steps.all()],
        })
    payload = json.dumps({'items': products, 'plans': plans}, ensure_ascii=False, indent=1)
    response = HttpResponse(payload, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inno_session_kopia.json"'
    return response


@login_required
def import_json(request):
    if request.method != 'POST' or not request.FILES.get('backup'):
        messages.error(request, 'Wybierz plik JSON do wczytania.')
        return redirect('inno_lab:base')
    try:
        payload = json.loads(request.FILES['backup'].read().decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        messages.error(request, 'Nie udało się odczytać pliku JSON.')
        return redirect('inno_lab:base')

    existing_keys = {(p.name, str(p.date or '')) for p in Product.objects.all()}
    added = 0
    for item in payload.get('items', []):
        key = (item.get('nazwa', ''), item.get('data', ''))
        if key in existing_keys or not item.get('nazwa'):
            continue
        date_val = item.get('data') or None
        try:
            date_val = datetime.date.fromisoformat(date_val) if date_val else None
        except ValueError:
            date_val = None
        Product.objects.create(
            source=Product.SOURCE_SESJA, date=date_val, name=item['nazwa'], brand=item.get('marka', ''),
            category=item.get('kat') if item.get('kat') in KATS else KATS[0],
            composition=item.get('sklad', ''), allergens=item.get('alergeny', ''), claims=item.get('claims', ''),
            whats_new=item.get('nowe', ''), appearance=item.get('wyglad', ''), conclusion=item.get('komentarz', ''),
            target_lines=item.get('targets') or [], created_by=request.user,
            **{k: (item.get('nutri') or {}).get(k, '') for k, _l, _u in NUTRI},
            **{k: (item.get('scores') or {}).get(k) for k, _l, _w in CRIT},
        )
        existing_keys.add(key)
        added += 1
    messages.success(request, f'Scalono kopię: dodano {added} ocen. Nic nie zostało nadpisane.')
    return redirect('inno_lab:base')


# --------------------------------------------------------------------------
# Transfer plan
# --------------------------------------------------------------------------

@login_required
def plan_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    plan = getattr(product, 'plan', None)

    if plan is None:
        if request.method == 'POST':
            form = NewPlanForm(request.POST)
            if form.is_valid():
                plan = TransferPlan.objects.create(
                    product=product, line=form.cleaned_data['line'],
                    flavour=form.cleaned_data['flavour'] or product.name,
                    start_date=form.cleaned_data['start_date'],
                )
                planning.build_plan_steps(plan, use_template=form.cleaned_data['use_template'] == '1')
                if product.target_lines != [NOPE] and plan.line not in product.target_lines:
                    product.target_lines = [l for l in product.target_lines if l != NOPE] + [plan.line]
                    product.save(update_fields=['target_lines'])
                messages.success(request, 'Action plan utworzony.')
                return redirect('inno_lab:plan', pk=product.pk)
        else:
            default_line = LINES[0]
            if product.target_lines and product.target_lines != [NOPE]:
                default_line = product.target_lines[0]
            form = NewPlanForm(initial={'line': default_line})
        return render(request, 'inno_lab/plan_new.html', {'product': product, 'form': form})

    steps = list(plan.steps.all())
    return render(request, 'inno_lab/plan_detail.html', {
        'product': product, 'plan': plan, 'steps': steps,
        'edit_form': PlanEditForm(instance=plan), 'new_step_form': NewStepForm(),
        'roles': ROLES, 'ai_enabled': settings.AI_FEATURES_ENABLED, 'ptypes': PTYPES,
        'owners_done': sum(1 for s in steps if s.initials),
    })


@login_required
def plan_edit(request, pk):
    plan = get_object_or_404(TransferPlan, pk=pk)
    if request.method == 'POST':
        old_line = plan.line
        form = PlanEditForm(request.POST, instance=plan)
        if form.is_valid():
            new_line = form.cleaned_data['line']
            new_start = form.cleaned_data['start_date']
            form.save()
            if new_line != old_line:
                planning.switch_line(plan, new_line)
                messages.success(request, f'Linia docelowa zmieniona na {new_line}. Krok próby technologicznej dopasowano do linii.')
            if new_start:
                planning.spread_dates(plan)
    return redirect('inno_lab:plan', pk=plan.product_id)


@login_required
def plan_recalc_progress(request, pk):
    plan = get_object_or_404(TransferPlan, pk=pk)
    if request.method == 'POST':
        plan.recompute_progress_from_steps()
        plan.save(update_fields=['progress', 'updated_at'])
    return redirect('inno_lab:plan', pk=plan.product_id)


@login_required
def plan_delete(request, pk):
    plan = get_object_or_404(TransferPlan, pk=pk)
    product_id = plan.product_id
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Action plan usunięty.')
    return redirect('inno_lab:plan', pk=product_id)


@login_required
def ai_enrich_plan(request, pk):
    plan = get_object_or_404(TransferPlan, pk=pk)
    if request.method == 'POST':
        try:
            data = ai_service.enrich_plan(plan)
        except ai_service.AIUnavailable as exc:
            messages.error(request, f'Uszczegółowienie AI niedostępne: {exc}')
        else:
            steps_by_nr = {s.nr: s for s in plan.steps.all()}
            for week in data.get('weeks', []):
                step = steps_by_nr.get(week.get('nr'))
                if not step:
                    continue
                if week.get('title'):
                    step.title = week['title']
                if week.get('tasks'):
                    step.tasks = week['tasks']
                step.save(update_fields=['title', 'tasks'])
            messages.success(request, 'Plan uszczegółowiony przez AI. Zweryfikuj zadania przed wysłaniem do zespołu.')
    return redirect('inno_lab:plan', pk=plan.product_id)


@login_required
def step_add(request, pk):
    plan = get_object_or_404(TransferPlan, pk=pk)
    if request.method == 'POST':
        form = NewStepForm(request.POST)
        if form.is_valid():
            last = plan.steps.order_by('-nr').first()
            nr = (last.nr + 1) if last else 1
            date = (last.date + datetime.timedelta(days=7)) if (last and last.date) else None
            PlanStep.objects.create(plan=plan, nr=nr, title=form.cleaned_data['title'],
                                     role=ROLES[1], tasks='', initials='', date=date)
    return redirect('inno_lab:plan', pk=plan.product_id)


@login_required
def step_edit(request, pk):
    step = get_object_or_404(PlanStep, pk=pk)
    product_id = step.plan.product_id
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'shift':
            delta = int(request.POST.get('delta', 0))
            if step.date:
                step.date = step.date + datetime.timedelta(days=delta)
                step.save(update_fields=['date'])
        elif action == 'today':
            step.date = timezone.localdate()
            step.save(update_fields=['date'])
        else:
            form = PlanStepForm(request.POST, instance=step)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.initials = (obj.initials or '').upper()[:4]
                obj.save()
    return redirect('inno_lab:plan', pk=product_id)


@login_required
def step_delete(request, pk):
    step = get_object_or_404(PlanStep, pk=pk)
    plan = step.plan
    product_id = plan.product_id
    if request.method == 'POST':
        step.delete()
        planning.renumber(plan)
    return redirect('inno_lab:plan', pk=product_id)


@login_required
def step_move(request, pk, direction):
    step = get_object_or_404(PlanStep, pk=pk)
    product_id = step.plan.product_id
    if request.method == 'POST':
        siblings = list(step.plan.steps.order_by('nr'))
        idx = siblings.index(step)
        swap_idx = idx - 1 if direction == 'up' else idx + 1
        if 0 <= swap_idx < len(siblings):
            other = siblings[swap_idx]
            step.nr, other.nr = other.nr, step.nr
            step.save(update_fields=['nr'])
            other.save(update_fields=['nr'])
    return redirect('inno_lab:plan', pk=product_id)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

@login_required
def dashboard(request):
    products = Product.objects.all()
    total = products.count()
    sesja = products.filter(source=Product.SOURCE_SESJA).count()
    archiwum = total - sesja
    selected = products.exclude(target_lines=[]).exclude(target_lines=[NOPE]).count()
    no_transfer = products.filter(target_lines=[NOPE]).count()
    ongoing = TransferPlan.objects.filter(progress__lt=100).count()
    done = TransferPlan.objects.filter(progress__gte=100).count()

    by_category = {}
    for p in products:
        cat = p.category or 'Inne'
        entry = by_category.setdefault(cat, {'n': 0, 'sum': 0.0})
        entry['n'] += 1
        entry['sum'] += float(p.overall_score or 0)
    category_avg = sorted(
        [{'kat': k, 'avg': v['sum'] / v['n'] if v['n'] else 0, 'n': v['n']} for k, v in by_category.items()],
        key=lambda x: -x['avg'],
    )
    max_avg = max([c['avg'] for c in category_avg], default=1) or 1

    top10 = products.order_by('-overall_score')[:10]

    crit_key = request.GET.get('crit', 'overall')
    crit_min = int(request.GET.get('min', 4))
    if crit_key == 'overall':
        crit_qs = products.filter(overall_score__gte=crit_min)
        crit_label = 'Ocena łączna'
    else:
        crit_qs = products.filter(**{f'{crit_key}__gte': crit_min})
        crit_label = dict((k, l) for k, l, _w in CRIT).get(crit_key, crit_key)
    crit_count = crit_qs.count()
    crit_results = crit_qs.order_by('-overall_score')[:25]

    plans_summary = TransferPlan.objects.select_related('product').all()

    return render(request, 'inno_lab/dashboard.html', {
        'total': total, 'sesja': sesja, 'archiwum': archiwum,
        'selected': selected, 'no_transfer': no_transfer,
        'ongoing': ongoing, 'done': done,
        'category_avg': category_avg, 'max_avg': max_avg,
        'top10': top10, 'crit': CRIT, 'crit_key': crit_key, 'crit_min': crit_min,
        'crit_label': crit_label, 'crit_count': crit_count, 'crit_results': crit_results,
        'crit_truncated': crit_count > 25,
        'plans_summary': plans_summary,
    })
