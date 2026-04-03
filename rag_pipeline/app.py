from rag_pipeline.retriever import HybridRetriever
from rag_pipeline.generator import ResponseGenerator
from rag_pipeline.config import Config
import argparse

class MOSDACBot:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.generator = ResponseGenerator()
        self._initialize()

    def _initialize(self):
        """Initialize the retriever"""
        print("Initializing SatSage...")
        self.retriever.index_documents()
        print("Knowledge graph and vector store ready!")

    def query(self, question: str) -> str:
        """Process user query and return response"""
        print(f"\nProcessing query: '{question}'")
        
        # Retrieve relevant context
        context = self.retriever.retrieve(question)
        print(f"Retrieved {len(context)} relevant documents")
        
        # Generate response
        response = self.generator.generate_response(question, context)
        return response

def main():
    parser = argparse.ArgumentParser(description="SatSage")
    parser.add_argument("--query", help="Direct query to process")
    args = parser.parse_args()

    bot = MOSDACBot()

    if args.query:
        print(bot.query(args.query))
    else:
        print("\nSatSage - Interactive Mode")
        print("Type 'exit' to quit\n")
        while True:
            try:
                question = input("Question: ")
                if question.lower() in ["exit", "quit"]:
                    break
                print("\n" + bot.query(question) + "\n")
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()