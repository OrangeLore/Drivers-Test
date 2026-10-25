"""Background runner for a full jurisdiction generation (grounded pipeline).
Usage: python run_jurisdiction.py <pdf> <key> <name> <jurisdiction> <target> <out.json> <log>"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generator

def main():
    pdf, key, name, juris, target, out, logf = sys.argv[1:8]
    def log(msg):
        with open(logf, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%H:%M:%S"), msg))
    def prog(i, total, count, msg):
        log("[%s/%s] %s" % (i, total, msg))
    log("START %s target=%s" % (name, target))
    try:
        ds = generator.run_full(pdf_bytes=open(pdf, "rb").read(),
                                meta={"key": key, "name": name, "jurisdiction": juris},
                                target=int(target), progress=prog)
        json.dump(ds, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        log("DONE %d questions (%d with grounding) -> %s" % (
            len(ds["questions"]), sum(1 for q in ds["questions"] if q.get("grounding")), out))
    except Exception as e:
        log("ERROR %s" % e)

if __name__ == "__main__":
    main()
