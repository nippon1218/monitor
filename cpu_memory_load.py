#!/usr/bin/env python3
"""
占用CPU和内存资源的示例脚本

这个脚本会创建多个工作线程来占用CPU资源，
并且会分配大量内存来测试内存监控功能。
"""

import os
import time
import argparse
import threading
import numpy as np
from multiprocessing import Pool, cpu_count

# 全局变量用于存储大型数组，防止被垃圾回收
memory_hogs = []

def cpu_intensive_task(duration=10):
    """
    执行CPU密集型计算任务
    
    Args:
        duration: 持续时间（秒）
    """
    start_time = time.time()
    while time.time() - start_time < duration:
        # 执行大量浮点运算来占用CPU
        for _ in range(10000000):
            _ = 1.0 * 2.0 ** 10 / 3.0

def memory_intensive_task(size_mb=100):
    """
    分配指定大小的内存
    
    Args:
        size_mb: 要分配的内存大小（MB）
    """
    # 创建大型NumPy数组并执行一些操作来确保它被使用
    # 每个双精度浮点数占8字节
    array_size = int(size_mb * 1024 * 1024 / 8)
    array = np.random.random(array_size)
    # 对数组执行一些操作
    array = array * 2 + 1
    # 将数组添加到全局列表中防止被垃圾回收
    global memory_hogs
    memory_hogs.append(array)
    return array.mean()

def run_cpu_load(num_threads, duration):
    """
    运行多个线程来占用CPU
    
    Args:
        num_threads: 线程数量
        duration: 每个线程运行的持续时间（秒）
    """
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=cpu_intensive_task, args=(duration,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    return threads

def run_memory_load(total_size_mb, chunks):
    """
    分配指定大小的内存，分成多个块
    
    Args:
        total_size_mb: 总内存大小（MB）
        chunks: 分块数量
    """
    chunk_size = total_size_mb // chunks
    for i in range(chunks):
        print(f"分配内存块 {i+1}/{chunks} ({chunk_size} MB)")
        memory_intensive_task(chunk_size)
        # 短暂暂停，让监控工具有时间捕获变化
        time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="CPU和内存负载生成器")
    parser.add_argument("--cpu", type=int, default=cpu_count(),
                        help="要使用的CPU线程数量（默认：所有可用核心）")
    parser.add_argument("--memory", type=int, default=500,
                        help="要分配的内存大小（MB）（默认：500MB）")
    parser.add_argument("--duration", type=int, default=60,
                        help="运行持续时间（秒）（默认：60秒）")
    parser.add_argument("--chunks", type=int, default=5,
                        help="内存分配的块数（默认：5）")
    
    args = parser.parse_args()
    
    print(f"===== CPU和内存负载生成器 =====")
    print(f"进程ID (PID): {os.getpid()}")
    print(f"CPU线程数: {args.cpu}")
    print(f"内存分配: {args.memory} MB")
    print(f"运行时间: {args.duration} 秒")
    print(f"内存分块: {args.chunks}")
    print("==============================")
    
    # 启动CPU负载线程
    print(f"启动 {args.cpu} 个CPU负载线程...")
    cpu_threads = run_cpu_load(args.cpu, args.duration)
    
    # 分配内存
    print(f"开始分配 {args.memory} MB 内存...")
    run_memory_load(args.memory, args.chunks)
    
    # 等待CPU线程完成
    start_time = time.time()
    elapsed = 0
    try:
        while elapsed < args.duration:
            remaining = args.duration - elapsed
            print(f"运行中... 剩余时间: {remaining:.1f} 秒")
            time.sleep(min(5, remaining))
            elapsed = time.time() - start_time
    except KeyboardInterrupt:
        print("用户中断，正在退出...")
    
    print("负载测试完成！")

if __name__ == "__main__":
    main()
