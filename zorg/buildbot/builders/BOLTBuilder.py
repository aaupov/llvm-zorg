from buildbot.plugins import steps
from zorg.buildbot.commands.CmakeCommand import CmakeCommand
from zorg.buildbot.builders.UnifiedTreeBuilder import getLLVMBuildFactoryAndSourcecodeSteps, addCmakeSteps, addNinjaSteps
from zorg.buildbot.process.factory import LLVMBuildFactory

def getBOLTCmakeBuildFactory(
           clean = False,
           bolttests = False,
           clangbolt = False,
           extra_configure_args = None,
           env = None,
           **kwargs):

    if env is None:
        env = dict()

    bolttests_dir = "bolt-tests"

    cleanBuildRequested = lambda step: clean or step.build.getProperty("clean", default=step.build.getProperty("clean_obj"))
    cleanBuildRequestedByProperty = lambda step: step.build.getProperty("clean")

    targets = ['bolt']
    checks = ['check-bolt']

    f = getLLVMBuildFactoryAndSourcecodeSteps(
            depends_on_projects=['bolt', 'llvm'],
            **kwargs) # Pass through all the extra arguments.

    if clangbolt:
        targets += ['clang++-bolt']
        checks = []
        CmakeCommand.applyRequiredOptions(cmake_options, [
            ("-C", "../" + src_dir + "/clang/cmake/caches/BOLT.cmake"),
            ])

    if bolttests:
        checks += ['check-large-bolt']
        extra_configure_args += [
            '-DLLVM_EXTERNAL_PROJECTS=bolttests',
            '-DLLVM_EXTERNAL_BOLTTESTS_SOURCE_DIR=' + LLVMBuildFactory.pathRelativeTo(bolttests_dir, f.monorepo_dir),
            ]
        # Clean checkout of bolt-tests if cleanBuildRequested
        f.addSteps([
            steps.RemoveDirectory(name="BOLT tests: clean",
                dir=bolttests_dir,
                haltOnFailure=True,
                warnOnFailure=True,
                doStepIf=cleanBuildRequestedByProperty),

            steps.Git(name="BOLT tests: checkout",
                description="fetching",
                descriptionDone="fetch",
                descriptionSuffix="BOLT Tests",
                repourl='https://github.com/rafaelauler/bolt-tests.git',
                workdir=bolttests_dir,
                alwaysUseLatest=True),
            ])

    # Some options are required for this build no matter what.
    CmakeCommand.applyRequiredOptions(extra_configure_args, [
        ('-G',                      'Ninja'),
        ])

    addCmakeSteps(
        f,
        cleanBuildRequested=cleanBuildRequested,
        extra_configure_args=extra_configure_args,
        obj_dir=None,
        env=env,
        **kwargs)

    addNinjaSteps(
        f,
        targets=targets,
        checks=checks,
        env=env,
        **kwargs)

    return f
