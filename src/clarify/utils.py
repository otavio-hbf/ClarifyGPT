import json
import os
import re
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
dotenv_path = os.path.abspath(dotenv_path)
load_dotenv(dotenv_path=dotenv_path)
MODEL_NAME = os.getenv("MODEL_NAME")

# -----------------------
# Helper: extract a section following a header, robust to:
# - optional ### prefix, plural/singular, optional colon, case-insensitive
# - stops at next markdown header (### ...) or end of text
def _extract_section(text: str, header_keywords: list[str]) -> str | None:
    if not text:
        return None
    txt = text.strip()

    # Find header line
    header_re = re.compile(
        r'^(?:\s*#{1,6}\s*)?(?:' + '|'.join(re.escape(k) for k in header_keywords) + r')\s*:?\s*$',
        re.IGNORECASE | re.MULTILINE,
    )
    m = header_re.search(txt)
    if not m:
        return None

    start = m.end()
    # Find next markdown header to bound the section
    next_header = re.compile(r'^\s*#{1,6}\s*[A-Za-z].*$', re.MULTILINE)
    n = next_header.search(txt, pos=start)
    end = n.start() if n else len(txt)

    body = txt[start:end].strip()
    return body if body else None
# -----------------------

def sort_parallel_datalines(data_lines):
    unsorted_data_line = [(int(json.loads(data_line)[0]['task_id']), data_line) for data_line in data_lines]
    sorted_data_line = sorted(unsorted_data_line, key=lambda x: x[0])
    data_lines = [item[1] for item in sorted_data_line]
    # print(len(data_lines))
    return data_lines


def getSignature(ori_prompt, entry_point):
    part_sig = '\ndef ' + entry_point
    part_sig_split = ori_prompt.split(part_sig)
    assert len(part_sig_split) == 2
    if part_sig_split[0].strip() == '':
        sig = ori_prompt.strip().split('\n')[0]
    else:
        assert len(ori_prompt.split(part_sig_split[0])) == 2
        sig = ori_prompt.split(part_sig_split[0])[-1].strip().split('\n')[0]
    assert sig[-1] == ':'
    return sig


def clean_format(generated_code):
    if "```" in generated_code:
        gen = generated_code.split("```")[1].strip()
        if gen.startswith("python"):
            gen = gen[len("python"):].strip()
    else:
        gen = generated_code

    return gen


def parse_code_w_prompt(model_name, generated_code, prompt, entry_point):
    if MODEL_NAME in model_name:
        gen = clean_format(generated_code)
        func_sig = 'def ' + entry_point + '('
        if gen.startswith(prompt.strip()):
            gen = gen.split(prompt.strip())[-1]
        elif func_sig in gen:
            gen_list = gen.split('\n')
            idx = 0
            for cur_gen in gen_list:
                if cur_gen.startswith(func_sig):
                    break
                else:
                    idx += 1
            if idx >= len(gen_list):
                gen = f"# CANNOT PARSE CODE SNIPPET\n{gen}"
                print(prompt)
                print(gen)
                assert 1 == 2
            gen = '\n'.join(gen_list[idx + 1:])
        else:
            gen = f"# CANNOT PARSE CODE SNIPPET\n{gen}"
            print(prompt)
            print(entry_point)
            print(gen)
            # assert 1 == 2
    else:
        pass
    return prompt + gen


def parse_code_w_prompt_mbpp(model_name, generated_code, prompt, entry_point):
    if MODEL_NAME in model_name:
        gen = clean_format(generated_code)
        func_sig = 'def ' + entry_point

        if func_sig in prompt:
            pre_func = prompt.split(func_sig)[0]
            gen = pre_func + gen
        else:
            gen = f"# CANNOT PARSE CODE SNIPPET\n{gen}"
            print(prompt)
            print(entry_point)
            print(gen)
    else:
        pass
    return gen


def parse_code_wo_prompt(model_name, generated_code, prompt, entry_point):
    if MODEL_NAME in model_name:
        gen = clean_format(generated_code)

        # Strip any trailing/leading whitespace from entry_point
        entry_point_clean = entry_point.strip()
        func_sig_pattern = f'def {entry_point_clean}'
        
        if gen.startswith(prompt.strip()):
            gen = gen.split(prompt.strip())[-1]
        elif func_sig_pattern in gen:
            gen_list = gen.split('\n')
            
            # Find the LAST occurrence of the function signature
            last_func_idx = -1
            for i, cur_gen in enumerate(gen_list):
                stripped_line = cur_gen.strip()
                # Check if line starts with "def entry_point" followed by optional space and parenthesis
                # This handles: "def func(", "def func (", "def func  ("
                if stripped_line.startswith(func_sig_pattern):
                    # Make sure it's followed by whitespace or parenthesis (not part of a longer name)
                    rest = stripped_line[len(func_sig_pattern):]
                    if rest and rest[0] in (' ', '('):
                        last_func_idx = i
            
            if last_func_idx == -1:
                # Fallback: try to find any line containing the function name
                print(f"# WARNING: Exact function signature not found, attempting flexible match")
                print(f"Looking for: {func_sig_pattern}")
                print(f"Generated code:\n{gen}")
                
                for i, line in enumerate(gen_list):
                    if f'def {entry_point_clean}' in line:
                        last_func_idx = i
                        break
                
                if last_func_idx == -1:
                    gen = f"# CANNOT PARSE CODE SNIPPET - No function definition found\n{gen}"
                    print("# FALLBACK FAILED - returning unparsed code")
                    return gen
            
            # Extract from the line AFTER the function definition
            gen = '\n'.join(gen_list[last_func_idx + 1:])
            
            # Clean up: remove docstrings and trailing content
            gen_lines = gen.split('\n')
            cleaned_lines = []
            in_docstring = False
            docstring_delimiter = None
            
            for line in gen_lines:
                stripped = line.strip()
                
                # Skip empty lines at the start
                if not cleaned_lines and not stripped:
                    continue
                
                # Track docstrings (handle both """ and ''')
                if not in_docstring:
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        docstring_delimiter = stripped[:3]
                        in_docstring = True
                        # Check if docstring closes on same line
                        if stripped.count(docstring_delimiter) >= 2:
                            in_docstring = False
                        continue
                else:
                    # We're inside a docstring, check if it closes
                    if docstring_delimiter in stripped:
                        in_docstring = False
                    continue
                
                # Stop if we hit another function definition
                if stripped.startswith('def ') and entry_point_clean not in stripped:
                    break
                
                cleaned_lines.append(line)
            
            gen = '\n'.join(cleaned_lines).strip()
            
        else:
            print("# WARNING: Function signature not found in generated code")
            print(f"Expected: {func_sig_pattern}")
            print(f"Prompt:\n{prompt}")
            print('---------------------------')
            print(f"Generated:\n{gen}")
            
            # Fallback: try to extract the first indented code block
            gen_list = gen.split('\n')
            idx = 0
            for cur_gen in gen_list:
                if cur_gen.startswith('    '):
                    break
                else:
                    idx += 1
            
            if idx < len(gen_list):
                gen = '\n'.join(gen_list[idx:])
            else:
                # Last resort: return the whole thing with a warning comment
                gen = f"# CANNOT PARSE CODE SNIPPET - Using full output\n{gen}"
    else:
        pass
    return gen


def parse_cq(model_name, generated_cq):
    if MODEL_NAME in model_name:
        if 'Clarifying Questions:' in generated_cq:
            cq = generated_cq.split('Clarifying Questions:')[-1]
        else:
            generated_cq_list = generated_cq.split('\n')
            idx = len(generated_cq_list)
            for i in list(reversed(range(len(generated_cq_list)))):
                if 'larify' in generated_cq_list[i] and 'uestions:' in generated_cq_list[i]:
                    break
                else:
                    idx -= 1
            if idx == 0:
                print('parse cq error')
                print(generated_cq)
                cq = 'No Questions.'
            else:
                cq = '\n'.join(generated_cq_list[idx:])
    else:
        pass
    return cq.strip()


def parse_cq_mbpp(generated_cq):
    # Prefer explicit headers; fall back to raw content
    section = _extract_section(
        generated_cq,
        ['clarifying question', 'clarifying questions', 'questions']
    )
    if section is not None:
        return section

    # If no header, try to drop any leading analysis and keep the last block
    if '###' in (generated_cq or ''):
        parts = re.split(r'\n###\s*[A-Za-z ]+:?\s*\n', generated_cq, flags=re.IGNORECASE)
        return parts[-1].strip()
    return (generated_cq or '').strip()

def parse_answer(model_name, generated_ans):
    # Robust answer extraction; return whole content if no header found
    section = _extract_section(
        generated_ans,
        ['answer', 'answers']
    )
    if section is not None:
        return section.strip()

    # Fallback: try to strip leading analysis sections
    txt = (generated_ans or '').strip()
    if '###' in txt:
        parts = re.split(r'\n###\s*[A-Za-z ]+:?\s*\n', txt, flags=re.IGNORECASE)
        return parts[-1].strip()
    return txt

def parse_clarification(generated_ask, generated_ans):
    # Use the robust MBPP CQ parser for all models
    generated_cq = parse_cq_mbpp(generated_ask)
    ans = parse_answer(MODEL_NAME, generated_ans)

    clarify_string = 'Clarification:\n'
    q_lines = [l.strip() for l in generated_cq.strip().split('\n') if l.strip()]
    a_lines = [l.strip() for l in ans.strip().split('\n') if l.strip()]

    if not q_lines or not a_lines or len(q_lines) != len(a_lines):
        clarify_string += ans.replace('\n\n', '\n').strip()
    else:
        for idx, (q_line, a_line) in enumerate(zip(q_lines, a_lines)):
            clarify_string += f'{q_line}\n{a_line.replace(f"{idx + 1}. ", "- ")}\n'
    return clarify_string.strip()

def parse_clarification_mbpp(generated_ask, generated_ans):
    txt = (generated_ans or '').strip()

    ans_body = _extract_section(txt, ['answer', 'answers'])
    if ans_body is None:
        # No explicit header; drop any leading analysis
        if '###' in txt:
            parts = re.split(r'\n###\s*[A-Za-z ]+:?\s*\n', txt, flags=re.IGNORECASE)
            ans_body = parts[-1].strip()
        else:
            ans_body = txt

    generated_cq = parse_cq_mbpp(generated_ask)

    clarify_string = 'Clarification:\n'
    q_lines = [l.strip() for l in generated_cq.strip().split('\n') if l.strip()]
    a_lines = [l.strip() for l in ans_body.strip().split('\n') if l.strip()]

    if not q_lines or not a_lines or len(q_lines) != len(a_lines):
        clarify_string += ans_body.replace('\n\n', '\n').strip()
    else:
        for idx, (q_line, a_line) in enumerate(zip(q_lines, a_lines)):
            clarify_string += f'{q_line}\n{a_line.replace(f"{idx + 1}. ", "- ")}\n'
    return clarify_string.strip()

def parse_explanation_mbpp(generated_ask, generated_ans):
    # Previously asserted a strict "### Answer" header; now robust.
    txt = (generated_ans or '').strip()
    ans_body = _extract_section(txt, ['answer', 'answers'])
    if ans_body is None:
        if '###' in txt:
            parts = re.split(r'\n###\s*[A-Za-z ]+:?\s*\n', txt, flags=re.IGNORECASE)
            ans_body = parts[-1].strip()
        else:
            ans_body = txt

    generated_cq = parse_cq_mbpp(generated_ask)
    explain_string = 'Explanation:\n'
    q_lines = [l.strip() for l in generated_cq.strip().split('\n') if l.strip()]
    a_lines = [l.strip() for l in ans_body.strip().split('\n') if l.strip()]

    if not q_lines or not a_lines or len(q_lines) != len(a_lines):
        explain_string += ans_body.replace('\n\n', '\n').strip()
    else:
        for idx, (q_line, a_line) in enumerate(zip(q_lines, a_lines)):
            explain_string += f'{q_line}\n{a_line.replace(f"{idx + 1}. ", "- ")}\n'
    return explain_string.strip()

def parse_synthesize(candidate_codes, generated_ask, generated_ans):
    # Remove strict header assertion and parse flexibly
    generated_cq = parse_cq_mbpp(generated_ask)
    ans = parse_answer(MODEL_NAME, generated_ans)

    clarify_string = 'Clarification:\n'
    q_lines = [l.strip() for l in generated_cq.strip().split('\n') if l.strip()]
    a_lines = [l.strip() for l in ans.strip().split('\n') if l.strip()]

    if not q_lines or not a_lines or len(q_lines) != len(a_lines):
        clarify_string += ans.replace('\n\n', '\n').strip()
    else:
        for idx, (q_line, a_line) in enumerate(zip(q_lines, a_lines)):
            clarify_string += f'{q_line}\n{a_line.replace(f"{idx + 1}. ", "- ")}\n'

    code_string = ''
    for idx, candidate_c in enumerate(candidate_codes):
        code_string += f'Solution {idx}:\n{candidate_c}\n'
    return clarify_string.strip() + '\n\n' + code_string.strip()

def parse_information_ignored(generated_ask):
    # Make header flexible
    section = _extract_section(
        generated_ask,
        ['information ignored', 'ignored information']
    )
    info = (section or (generated_ask or '')).strip()
    clarify_string = 'Clarification:\n' + info
    return clarify_string.strip()

def refine_prompt_clarify(ori_prompt, clarification):
    ori_prompt = ori_prompt.strip()
    assert ori_prompt[-7:] == "    '''"

    clarify_list = clarification.split('\n')
    clarification = '    ' + '\n    '.join(clarify_list) + '\n'
    refined_prompt = ori_prompt[:-7] + clarification + "    '''"
    return refined_prompt