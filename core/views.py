from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.conf import settings
import subprocess
import json
import os


def index(request):
    return render(request, 'index.html')


@require_POST
def manage_client(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        else:
            data = request.POST.dict()
    except Exception:
        return HttpResponseBadRequest('Invalid body')

    action = data.get('action')
    client = data.get('client')
    port = data.get('port')
    ports = data.get('ports')

    allowed = {'delete', 'create', 'stop', 'restart', 'restart-port', 'extend'}
    if action not in allowed:
        return HttpResponseBadRequest('Invalid action')
    if not client:
        return HttpResponseBadRequest('Missing client')

    bin_path = '/usr/local/bin/manage_client'
    if not os.path.exists(bin_path):
        alt = os.path.join(settings.BASE_DIR, 'manage_client.sh')
        bin_path = alt if os.path.exists(alt) else bin_path

    cmd = [bin_path, action, client]
    if action == 'create':
        in_port = data.get('in_port')
        extra_ports = []
        if isinstance(ports, list):
            extra_ports = ports
        elif isinstance(ports, str) and ports.strip():
            extra_ports = ports.strip().split()
        if isinstance(in_port, str):
            cmd.append(in_port)
        elif isinstance(in_port, int):
            cmd.append(str(in_port))
        if extra_ports:
            cmd.extend([str(p) for p in extra_ports])
    elif action == 'restart-port':
        if not port:
            return HttpResponseBadRequest('Missing port')
        cmd.append(str(port))
    elif action == 'extend':
        extra_ports = []
        if isinstance(ports, list):
            extra_ports = ports
        elif isinstance(ports, str) and ports.strip():
            extra_ports = ports.strip().split()
        if not extra_ports:
            return HttpResponseBadRequest('Missing ports')
        cmd.extend([str(p) for p in extra_ports])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return JsonResponse({
            'ok': proc.returncode == 0,
            'returncode': proc.returncode,
            'stdout': proc.stdout,
            'stderr': proc.stderr,
            'command': cmd,
        })
    except FileNotFoundError:
        return JsonResponse({'ok': False, 'error': 'Command not found', 'command': cmd}, status=500)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
