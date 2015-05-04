
import json
import pprint


def assert_event_matches(expected, actual, tolerate=None):
    """
    Compare two event dictionaries.

    Fail if any discrepancies exist, and output the list of all discrepancies. The intent is to produce clearer
    error messages than "{ some massive dict } != { some other massive dict }", instead enumerating the keys that
    differ. Produces period separated "paths" to keys in the output, so "context.foo" refers to the following
    structure:

        {
            'context': {
                'foo': 'bar'  # this key, value pair
            }
        }
    """
    differences = get_event_differences(expected, actual, tolerate=tolerate)
    if len(differences) > 0:
        debug_info = [
            '',
            'Expected:',
            block_indent(expected),
            'Actual:',
            block_indent(actual),
            'Tolerating:',
            block_indent(get_tolerate_or_default(tolerate)),
        ]
        differences = ['* ' + d for d in differences]
        message_lines = differences + debug_info
        raise AssertionError('Unexpected differences found in structs:\n\n' + '\n'.join(message_lines))


def assert_events_equal(expected, actual):
    """
    Strict comparison of two events.

    This asserts that every field in the real event exactly matches the expected event.
    """
    assert_event_matches(expected, actual, tolerate=frozenset())


def get_event_differences(expected, actual, tolerate=None):
    tolerate = get_tolerate_or_default(tolerate)

    # Some events store their payload in a JSON string instead of a dict. Comparing these strings can be problematic
    # since the keys may be in different orders, so we parse the string here if we were expecting a dict.
    if 'string_payload' in tolerate:
        expected = parse_event_payload(expected.copy())
        actual = parse_event_payload(actual.copy())

    def should_strict_compare(path):
        """
        We want to be able to vary the degree of strictness we apply depending on the testing context.

        Some tests will want to assert that the entire event matches exactly, others will tolerate some variance in the
        context or root fields, but not in the payload (for example).
        """
        if path == [] and 'root_extra_fields' in tolerate:
            return False
        elif path == ['event'] and 'payload_extra_fields' in tolerate:
            return False
        elif path == ['context'] and 'context_extra_fields' in tolerate:
            return False
        else:
            return True

    return compare_structs(expected, actual, should_strict_compare=should_strict_compare)


def block_indent(text, spaces=4):
    return '\n'.join([(' ' * spaces) + l for l in pprint.pformat(text).splitlines()])


def get_tolerate_or_default(tolerate=None):
    tolerate_by_default = {
        'string_payload',
        'root_extra_fields',
        'context_extra_fields',
        # NOTE: "payload_extra_fields" is deliberately excluded from this list since we want to detect erroneously added
        # fields in the payload.
    }

    if tolerate is None:
        tolerate = tolerate_by_default

    return tolerate


def parse_event_payload(event):
    if 'event' in event and isinstance(event['event'], basestring):
        try:
            event['event'] = json.loads(event['event'])
        except ValueError:
            pass
    return event


def compare_structs(expected, actual, should_strict_compare=None, path=None):
    if path is None:
        path = []
    differences = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = frozenset(expected.keys())
        actual_keys = frozenset(actual.keys())

        for key in (expected_keys - actual_keys):
            differences.append('{0}: not found in actual'.format(_path_to_string(path + [key])))

        if should_strict_compare is not None and should_strict_compare(path):
            for key in (actual_keys - expected_keys):
                differences.append('{0}: only defined in actual'.format(_path_to_string(path + [key])))

        for key in (expected_keys & actual_keys):
            child_differences = compare_structs(expected[key], actual[key], should_strict_compare, path + [key])
            differences.extend(child_differences)

    elif expected != actual:
        differences.append('{path}: {a} != {b} (expected != actual)'.format(
            path=_path_to_string(path),
            a=repr(expected),
            b=repr(actual)
        ))

    return differences


def is_matching_event(expected_event, actual_event, tolerate=None):
    return len(get_event_differences(expected_event, actual_event, tolerate=tolerate)) == 0


def _path_to_string(path):
    return '.'.join(path)
