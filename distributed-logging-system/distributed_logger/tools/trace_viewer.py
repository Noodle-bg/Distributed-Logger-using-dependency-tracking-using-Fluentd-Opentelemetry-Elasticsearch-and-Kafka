from collections import defaultdict
from datetime import datetime
import json
import sys

class TraceViewer:
    def __init__(self):
        self.traces = defaultdict(list)
        
    def add_trace(self, trace_data):
        """Add a trace entry to the viewer"""
        trace_id = trace_data.get('trace_id')
        if trace_id:
            self.traces[trace_id].append(trace_data)
    
    def display_trace(self, trace_id):
        """Display a single trace with its spans"""
        spans = self.traces[trace_id]
        if not spans:
            return
            
        print(f"\nTrace ID: {trace_id}")
        print("=" * 50)
        
        for span in sorted(spans, key=lambda x: x['timestamp']):
            source = span['source_service']
            target = span['target_service']
            status = span['status']
            timestamp = datetime.fromisoformat(span['timestamp'])
            
            # Format the display
            print(f"{timestamp.strftime('%H:%M:%S.%f')[:-3]} "
                  f"{source} → {target} [{status}]")
            
            if status == "FAILED" and 'error_details' in span:
                print(f"  Error: {span['error_details'].get('error_message', 'Unknown error')}")
                
        print("-" * 50)

    def display_all_traces(self):
        """Display all traces"""
        print(f"\nFound {len(self.traces)} traces:")
        for trace_id in self.traces:
            self.display_trace(trace_id)

def main():
    viewer = TraceViewer()
    
    # Read trace logs from stdin
    for line in sys.stdin:
        try:
            trace_data = json.loads(line)
            viewer.add_trace(trace_data)
        except json.JSONDecodeError:
            continue
    
    viewer.display_all_traces()

if __name__ == "__main__":
    main()