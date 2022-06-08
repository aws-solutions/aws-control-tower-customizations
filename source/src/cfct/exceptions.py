class StackSetHasFailedInstances(Exception):
    def __init__(self, stack_set_name: str, failed_stack_set_instances):
        self.stack_set_name = stack_set_name
        self.failed_stack_set_instances = failed_stack_set_instances
