# monitor

## 需求v0.1.0
- 使用python对指定的进程进行监控
    - 进程列表在配置文件中指定,yaml格式
    - 监控内容包括:进程cpu, 进程内存(rss占用), 进程状态 
    - 统计每个CPU的使用率
    - 统计系统的cpu负载
    - 使用psutil进行监控, 每10s进行一次监控
    - 将统计结果保存成csv文件 
    - 使用poltly进行可视化, 将可视化结果保存成html文件
        - 每个核心的cpu使用率单独使用一个图表，并且放在独立的html文件中
        - 全部cpu的图表都集中到1个html文件中。只需要生成2个html，一个html中是cpu的图，另一个是其他图
    - 支持实时网页展示(使用flask), 可以实时查看监控结果， 参数配置文件中指定是否开启,默认不开启
    - 支持systemd服务启动
    - 使用weasyprint将html转换成pdf