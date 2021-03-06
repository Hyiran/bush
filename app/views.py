# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.utils.timezone import now
from app.models import *

from utils import generate_xml
from staf_wrapper.wrapper_STAF import STAFWrapper,staf_obj

import os
import tasks
import pprint

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect(reverse("suite_list"))
        else:
            return render(request, "login.html", locals())

    else:
        return render(request, "login.html", locals())

def logout_view(request):
    logout(request)
    return redirect(request.META.get("HTTP_REFERER", reverse("task_list")))

def suite_list(request):
    error = None
    suites = None
    if request.method == "POST":
        p_name = request.POST['name']
        p_description = request.POST['description']
        p_suites = request.POST['catgory']
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            suite = Suite(name=p_name, description=p_description, createdAt=now())
            suite.save()
            # for p_suite in p_suites:
            #     suite.suites.add(Suite.objects.get(name=p_suite))
    if Suite.objects.exists():
        suites = Suite.objects.all()

    return render(request, "suite.html", locals())

def suite_create(request):
    if request.method == "POST":
        p_name = request.POST['name']
        p_description = request.POST['description']
        #p_suites = request.POST['catgory']
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            suite = Suite(name=p_name, description=p_description, createdAt=now())
            suite.save()
            # for p_suite in p_suites:
            #     suite.suites.add(Suite.objects.get(name=p_suite))
        return redirect(reverse("suite_list"))
    return render(request, "suite_create.html", locals())

def suite_view(request, pk):
    suite = Suite.objects.get(pk = pk)
    suites = None
    p_suite = Suite.objects.get(id=pk)
    p_cases = p_suite.cases.all()

    # if request.method == "POST":
    #     p_id = request.POST['case']
    #     p_case = Case.objects.get(id=p_id)
    #     Task_Case(case=p_case, task=p_suite).save()

    # child_cases = Task_Case.objects.filter(task=p_suite)

    task_reports = Task_Report.objects.filter(task=p_suite)
    if task_reports:
        task_report = Task_Report.objects.filter(task=p_suite).order_by('-id')[0]
        machine = Machine.objects.all()[0]
    # cases = Case.objects.filter(suite=p_suite).exclude(task_case__in=child_cases.values_list("id", flat=True))
    return render(request, "suite_view.html", locals())

def get_f_suite(suites, suites_list):
    if not suites:
        return
    else:
        for suite in suites:
            suites_list.extend(suite.suite_set.all())
            get_f_suite(suite.suite_set.all(), suites_list)

def get_sub_suite(suites, suites_list):
    if not suites:
        return
    else:
        for suite in suites:
            suites_list.extend(suite.suites.all())
            get_sub_suite(suite.suites.all(), suites_list)

def add_suite_view(request, pk):
    a_suites = Suite.objects.all()
    f_suites = Suite.objects.filter(pk=pk)
    c_suite = f_suites[0].suites.all()

    father_suites = f_suites[0].suite_set.all()
    father_suites_list = list(father_suites)

    get_f_suite(father_suites, father_suites_list)
    father_suites_list = list(set(father_suites_list))


    suites = [suite for suite in a_suites if ((suite not in f_suites) & (suite not in father_suites_list) & (suite not in c_suite))]

    return render(request, "suite_add.html", {"suites": suites, "f_suite": f_suites[0]})

def add_suite(request, f_suite_pk, suite_pk):
    f_suite = Suite.objects.filter(pk=f_suite_pk)[0]
    suite = Suite.objects.filter(pk=suite_pk)[0]

    sub_suites = suite.suites.all()
    sub_suites_list = list(sub_suites)

    get_sub_suite(sub_suites, sub_suites_list)
    sub_suites_list = list(set(sub_suites_list))

    if f_suite not in sub_suites_list:
        f_suite.suites.add(suite)
    else:
        # suites = Suite.objects.all()
        # return render(request, "suite_add_404.html", {"suites": suites, "f_suite": f_suite})
        print 123
        # TBD: need to return a prompt that hint user this is the "Ring graph"

    a_suites = Suite.objects.all()
    f_suites = Suite.objects.filter(pk=f_suite.pk)
    c_suite = f_suites[0].suites.all()

    suites = [suite for suite in a_suites if ((suite not in f_suites) & (suite not in sub_suites_list) & (suite not in c_suite))]

    return render(request, "suite_add.html", {"suites": suites, "f_suite": f_suites[0]})

def add_case_view(request, pk):
    a_cases = Case.objects.all()
    f_suites = Suite.objects.filter(pk=pk)
    c_cases = f_suites[0].cases.all()

    # pprint.pprint(a_cases,c_cases)

    cases = [case for case in a_cases if (case not in c_cases)]

    return render(request, "case_add.html", {"cases":cases,"f_suite":f_suites[0]})

def add_case(request, f_suite_pk, case_pk):
    f_suite = Suite.objects.filter(pk=f_suite_pk)[0]
    case = Case.objects.filter(pk=case_pk)[0]

    f_suite.cases.add(case)
    f_suite.save()

    a_cases = Case.objects.all()
    f_suites = Suite.objects.filter(pk=f_suite_pk)
    c_cases = f_suites[0].cases.all()

    cases = [case for case in a_cases if (case not in c_cases)]

    return render(request, "case_add.html", {"cases": cases, "f_suite": f_suites[0]})

def suite_edit(request, pk):
    suite = Suite.objects.get(pk = pk)
    if request.method == "POST":
        suites = Suite.objects.all()
        p_name = request.POST.get('name')
        p_description = request.POST.get('description')
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            suite.name = p_name
            suite.description = p_description
            suite.save()
            return render(request, "suite.html", locals())

    return render(request, "suite_edit.html", locals())

def suite_remove(request,pk ,suite_pk):
    suite = Suite.objects.get(pk = pk)
    suite_del = Suite.objects.get(pk = suite_pk)

    suite.suites.remove(suite_del)
    suite.save()

    suite = Suite.objects.get(pk = pk)
    return render(request, "suite_view.html", {"suite":suite})


def suite_delete(request, pk):
    Suite.objects.get(pk=pk).delete()
    return redirect(reverse("suite_list"))

def suite_case_delete(request, pk_suite, pk_case):
    p_suite = Suite.objects.get(id=pk_suite)
    p_case = Case.objects.get(id=pk_case)
    p_suite.cases.remove(p_case)
    return redirect(reverse("suite_view", kwargs={"pk": pk_suite}))

def case_list(request):
    # p_suite = None
    # cases = None
    # suites = None

    # if Suite.objects.exists():
        # p_suite = Suite.objects.all().order_by('id')[0]
        # suites = Suite.objects.all()
    cases = Case.objects.all()
    return render(request, "case.html", locals())


def case_list_index(request, pk):
    # p_suite = None
    # suites = None
    # cases = None
    # if Suite.objects.exists():
    # suites = Suite.objects.all()
    # p_suite = Suite.objects.get(id=pk)
    cases = Case.objects.all().order_by('id')
    return render(request, "case.html", locals())

def case_create(request):
    # p_suite = Suite.objects.get(id=pk)
    # suites = Suite.objects.all()
    if request.method == "POST":
        p_name = request.POST['name']
        p_level = request.POST['level']
        # p_suites = request.POST['suites']
        # p_suite = Suite.objects.get(id=pk)
        p_command = request.POST['command']
        p_script = request.POST['script']
        p_param = request.POST['param']
        p_description = request.POST['description']
        if p_name == "" or p_command == "" or p_description == "":
            error = "数据不能为空"
        else:
            # for p_suite in p_suites:
            case = Case(name=p_name, level=p_level, command=p_command,
                 script=p_script, param=p_param, description=p_description, createdAt=now())
            case.save()
                # case.suites.add(p_suite)
            return redirect(reverse("case_list_index", kwargs={"pk": case.pk}))
    return render(request, "case_create.html", locals())

def case_view(request, pk):
    case = None
    suites = None
    if Suite.objects.exists():
        case = Case.objects.get(id=pk)
        suites = Suite.objects.all()
    return render(request, "case_view.html", locals())

def case_delete(request, pk):
    Case.objects.get(id=pk).delete()
    return redirect(reverse("case_list"))

def case_remove(request, pk, case_pk):
    suite = Suite.objects.get(pk = pk)
    case_del = Case.objects.get(pk = case_pk)

    suite.cases.remove(case_del)
    suite.save()

    suite = Suite.objects.get(pk = pk)
    return render(request, "suite_view.html", {"suite":suite})

def case_edit(request, pk):
    suites = None
    case = None
    case = Case.objects.get(id=pk)

    if request.method == "POST":
        p_name = request.POST['name']
        p_level = request.POST['level']
        # p_suites = request.POST['suites']
        p_command = request.POST['command']
        p_script = request.POST['script']
        p_param = request.POST['param']
        p_description = request.POST['description']
        if p_name == "" or p_command == "" or p_description == "":
            error = "数据不能为空"
        else:
            case.name = p_name
            case.level = p_level
            case.command = p_command
            case.script = p_script
            case.param = p_param
            case.description = p_description
            case.modifyAt = now()
            case.save()
        #    case.suites.clear()
        #    for p_suite in p_suites:
        #        case.suites.add(p_suite)
            return redirect(reverse("case_view", kwargs={"pk": pk}))
    else:
        if Suite.objects.exists():
            suites = Suite.objects.all()
        return render(request, "case_edit.html", locals())

# def task_list(request):
#     p_suite = None
#     suites = None
#     p_tasks = None
#     if Suite.objects.exists():
#         p_suite = Suite.objects.all().order_by('id')[0]
#         suites = Suite.objects.all()
#         p_tasks = Task.objects.filter(suite=p_suite)
#     return render(request, "task.html", locals())
#
# def task_list_index(request, pk):
#     p_suite = None
#     suites = None
#     p_tasks = None
#     if Suite.objects.exists():
#         p_suite = Suite.objects.get(id=pk)
#         suites = Suite.objects.all()
#         p_tasks = Task.objects.filter(suite=p_suite).order_by('id')
#     return render(request, "task.html", locals())
#
# def task_create(request, pk):
#     p_suite = Suite.objects.get(id=pk)
#     suites = Suite.objects.all()
#     cases = Case.objects.filter(suite=p_suite).order_by('id')
#     if request.method == "POST":
#         p_name = request.POST['name']
#         p_description = request.POST['description']
#         p_num = request.POST['num']
#         if p_name == "" or p_description == "":
#             error = "数据不能为空"
#         else:
#             Task(name=p_name, suite=p_suite, description=p_description, createdAt=now()).save()
#             p_task = Task.objects.get(name=p_name)
#         for num in range(0, int(p_num)):
#             case_id = request.POST['case'+str(num)]
#             p_case = Case.objects.get(id=case_id)
#             Task_Case(task=p_task, case=p_case, createdAt=now()).save()
#             # child_cases = Task_Case.objects.filter(task=p_task)
#             # generate_xml(p_task.name, child_cases)
#
#         return redirect(reverse("task_list_index", kwargs={"pk": pk}))
#     return render(request, "task_create.html", locals())
#
# def task_view(request, pk):
#     suites = None
#     p_task = Task.objects.get(id=pk)
#     p_cases = Task_Case.objects.filter(task=p_task)
#
#     if Suite.objects.exists():
#         suites = Suite.objects.all()
#         p_task = Task.objects.get(id=pk)
#         p_task_cases = Task_Case.objects.filter(task=p_task)
#     if request.method == "POST":
#         p_id = request.POST['case']
#         p_case = Case.objects.get(id=p_id)
#         Task_Case(case=p_case, task=p_task).save()
#         # child_cases = Task_Case.objects.filter(task=p_task)
#         # generate_xml(p_task.name, child_cases)
#     child_cases = Task_Case.objects.filter(task=p_task)
#
#     task_reports = Task_Report.objects.filter(task=p_task)
#     if task_reports:
#         task_report = Task_Report.objects.filter(task=p_task).order_by('-id')[0]
#         machine = Machine.objects.get(suite=p_task.suite)
#     cases = Case.objects.filter(suite=p_task.suite).exclude(task_case__in=child_cases.values_list("id", flat=True))
#     return render(request, "task_view.html", locals())
#
# def task_edit(request, pk):
#     suites = None
#     p_cases = None
#     p_task_cases = None
#     p_task = Task.objects.get(id=pk)
#     p_task_cases = Task_Case.objects.filter(task=p_task)
#     if Suite.objects.exists():
#         suites = Suite.objects.all()
#         p_cases = Case.objects.filter(suite=p_task.suite)
#     if request.method == "POST":
#         p_name = request.POST['name']
#         p_description = request.POST['description']
#         p_num = request.POST['num']
#         if p_name == "" or p_description == "":
#             error = "数据不能为空"
#         p_task.name = p_name
#         p_task.description = p_description
#         p_task.save()
#         for num in range(0, int(p_num)):
#             case_id = request.POST['case'+str(num)]
#             p_case = Case.objects.get(id=case_id)
#             Task_Case(task=p_task, case=p_case, createdAt=now()).save()
#         p_task_cases = Task_Case.objects.filter(task=p_task)
#
#     return render(request, "task_edit.html", locals())

def get_cases(p_suites, child_cases_list):
    if not p_suites:
        return
    else:
        for p_suite in p_suites:
            child_cases_list.extend(p_suite.cases.all())
            get_cases(p_suite.suites.all(), child_cases_list)

def task_trigger(request, pk):
    p_suite = Suite.objects.get(id=pk)
    # assume the first machine is ok!
    p_machine = Machine.objects.all()[0]
    machine_ip = p_machine.address
    task_name = p_suite.name

    child_cases = p_suite.cases.all()
    child_cases_list = list(child_cases)
    get_cases(p_suite.suites.all(), child_cases_list)
    child_cases = list(set(child_cases_list))


    task_report = Task_Report(task=p_suite, machine=p_machine)
    task_report.save()

    p_task_report = Task_Report.objects.get(id=task_report.id)
    generate_xml(p_suite.name, child_cases, task_report.id)

    exec_handle = staf_obj.execute(task_name, machine_ip)
    tasks.monitor.delay(staf_obj, exec_handle, p_task_report, machine_ip)

    task_report = Task_Report.objects.all().order_by('-createdAt')[0]
    case_reports = task_report.case_report_set.all()
    return redirect(reverse("report_task_list", kwargs={"pk": pk}))

# def task_delete(request, pk):
#     p_task = Task.objects.get(id=pk)
#     Task_Case.objects.filter(task=p_task).delete()
#     Task.objects.get(id=pk).delete()
#     return redirect(reverse("task_list"))

def task_case_delete(request, pk_task, pk_case):
    p_task = Task.objects.get(id=pk_task)
    p_case = Case.objects.get(id=pk_case)
    Task_Case.objects.filter(task=p_task).get(case=p_case).delete()
    return redirect(reverse("task_edit", kwargs={"pk": pk_task}))

def machine_list(request):
    suites = None
    p_suite = None
    machines = None
    # if Suite.objects.exists():
    #     suites = Suite.objects.all()
    #     p_suite = Suite.objects.all().order_by('id')[0]
    #     machines = Machine.objects.filter(suite=p_suite).order_by('id')
    machines = Machine.objects.order_by('id')
    if request.method == "POST":
        p_name = request.POST['name']
        p_description = request.POST['description']
        p_address = request.POST['address']
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            Machine(name=p_name, description=p_description, address=p_address, createdAt=now()).save()
    return render(request, "machine.html", locals())

# def machine_list_index(request, pk):
#     p_suite = None
#     suites = None
#     machines = None
#     if Suite.objects.exists():
#         p_suite = Suite.objects.get(id=pk)
#         suites = Suite.objects.all()
#         machines = Machine.objects.filter(suite=p_suite).order_by('id')
#     return render(request, "machine.html", locals())

def machine_view(request, pk):
    p_machine = Machine.objects.get(id=pk)
    suites = Suite.objects.all()
    return render(request, "machine_view.html", locals())

def machine_create(request):
    suites = Suite.objects.all()
    if request.method == "POST":
        p_name = request.POST['name']
        p_description = request.POST['description']
        p_address = request.POST['address']
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            Machine(name=p_name, description=p_description, address=p_address, createdAt=now()).save()
            return redirect(reverse("machine_list"))
    return render(request, "machine_create.html", locals())

def machine_edit(request, pk):
    suites = None
    p_suite = None

    if Suite.objects.exists():
        suites = Suite.objects.all()
        p_machine = Machine.objects.get(id=pk)
    if request.method == "POST":
        p_name = request.POST['name']
        p_address = request.POST['address']
        p_description = request.POST['description']
        if p_name == "" or p_description == "":
            error = "数据不能为空"
        else:
            p_machine.name = p_name
            p_machine.address = p_address
            p_machine.description = p_description
            p_machine.modifyAt = now()
            p_machine.save()
            return redirect(reverse("machine_view", kwargs={"pk": pk}))
    else:
        return render(request, "machine_edit.html", locals())

def machine_delete(request, pk):
    Machine.objects.get(id=pk).delete()
    return redirect(reverse("machine_list"))

def script_list(request):
    script_path = settings.MEDIA_ROOT + settings.SCRIPT_DIR
    if request.method == "POST":
        p_file = request.FILES['name']
        open(script_path + p_file.name, 'wb').write(p_file.read())
    scripts = os.listdir(script_path)
    return render(request, "script.html", locals())

def script_view(request):
    g_name = request.GET['name']
    script_path = settings.MEDIA_ROOT + settings.SCRIPT_DIR + g_name

    try:
        script = open(script_path)
        script_text = script.read()
    finally:
        script.close()
    return render(request, "script_view.html", locals())

def script_add(request):
    if request.method == "POST":
        p_file = request.FILES['name']
        script_path = settings.MEDIA_ROOT + settings.SCRIPT_DIR
        open(script_path + p_file.name, 'wb').write(p_file.read())
        return redirect(reverse("script_view"))

def report_list(request):
    suites = Suite.objects.order_by('id')
    return render(request, "report.html", locals())

def report_task_list(request, pk):
    suites = Suite.objects.all()
    p_suite = Suite.objects.get(id=pk)
    task_reports = Task_Report.objects.filter(task=p_suite).order_by('id')
    return render(request, "report_task.html", locals())

def report_task_view(request, pk):
    suites = Suite.objects.all()
    p_task_report = Task_Report.objects.get(id=pk)
    case_reports = p_task_report.case_report_set.all().order_by('id')
    return render(request, "report_view.html", locals())

def report_case_log_view(request):
    g_task_report_id = request.GET['id']
    log_name = request.GET['name'] + '.log'
    log_path = os.path.expanduser(r'~/log/{}'.format(g_task_report_id))
    log_location = os.path.join(log_path, log_name)

    try:
        log_handle = open(log_location)
        log_text = log_handle.read()
    finally:
        log_handle.close()
    return render(request, "log_view.html", locals())


def demo_celery(request):
    print 123
    #from tasks import add
    add.delay(2, 2)
    print 778
