"""Explicit run limits and measurements; portable mode never emulates POSIX."""
import os
import platform
import sys
import time
try:
    import resource
except ImportError:
    resource = None


def environment():
    return {'python': sys.version, 'executable': sys.executable,
            'os': platform.platform(), 'machine': platform.machine(),
            'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
            'optimization': sys.flags.optimize}


def enforce_limits(portable=False):
    if portable:
        return {'mode': 'portable', 'cpu_limit_seconds': None,
                'address_space_mib': None, 'affinity_pinned': False,
                'reason': 'Explicit opt-in; POSIX CPU/address-space guards not executed.'}
    if resource is None:
        raise ValueError('POSIX resource unavailable; use --portable explicitly. '
                         'Portable mode has no CPU/address-space guard.')
    pinned = hasattr(os, 'sched_setaffinity')
    if pinned:
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (3584*1024**2, 3584*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    return {'mode': 'posix', 'cpu_limit_seconds': 40,
            'address_space_mib': 3584, 'affinity_pinned': pinned}


def rss_kib(who='self'):
    if resource is None:
        return None
    target = resource.RUSAGE_SELF if who == 'self' else resource.RUSAGE_CHILDREN
    value = resource.getrusage(target).ru_maxrss
    return value/1024 if sys.platform == 'darwin' else value


def child_cpu():
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def measurement(cpu_start, wall_start, limits):
    return {'cpu_seconds': time.process_time()-cpu_start,
            'wall_seconds': time.perf_counter()-wall_start,
            'peak_rss_kib': rss_kib(), 'workers': 1,
            'environment': environment(), 'limits': limits}
