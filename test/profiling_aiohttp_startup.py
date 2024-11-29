import lk_logger
print(':t')
import line_profiler
print(':t')


@line_profiler.profile
def main():
    import aiohttp
    import aiohttp.web
    print('start', ':t')
    import airmise as air
    # air.Server().run({
    #     'aaa': 111,
    #     'bbb': [],
    #     'ccc': lambda: print('hello')
    # })
    print(air, ':t')


if __name__ == '__main__':
    main()
