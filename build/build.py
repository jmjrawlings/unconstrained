"""
build.py

Key build scripts constructed as a dagger pipeline.
"""

import anyio
import dagger
import sys

config = dagger.Config(log_output=sys.stderr)
platform = dagger.Platform("linux/amd64")

async def test():
    async with dagger.Connection(config) as client:
        root = client.host().directory(".")

        async def build_container(target):
            con = await client \
                .pipeline("build-containers") \
                .container(platform=platform) \
                .pipeline(target) \
                .build(root, target=target) \
                .stdout()
            
            return con

        await build_container("prod")
        await build_container("test")
        await build_container("dev")

anyio.run(test)