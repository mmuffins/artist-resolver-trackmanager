                "joinphrase" not in reordered_data[i].keys()
                or "joinphrase" not in reordered_data[i + 1].keys()
                continue

            if cv_pattern.match(reordered_data[i]["joinphrase"]) and reordered_data[
                i + 1
            ]["joinphrase"].startswith(")"):
