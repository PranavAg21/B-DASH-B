from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Dataset
from .serializers import DatasetSerializer
import pandas as pd
from django.conf import settings

# ✅ TRY Gemini (optional)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False


# -------------------------------
# 📂 DATASET LIST API
# -------------------------------
@api_view(['GET', 'POST'])
def dataset_list(request):
    if request.method == 'GET':
        data = Dataset.objects.all()
        serializer = DatasetSerializer(data, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DatasetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


# -------------------------------
# 📊 READ CSV DATA
# -------------------------------
@api_view(['GET'])
def dataset_data(request, id):
    try:
        dataset = Dataset.objects.get(id=id)
        file_path = dataset.file.path

        df = pd.read_csv(file_path)
        data = df.to_dict(orient='records')

        return Response(data)

    except Exception as e:
        print("🔥 DATA ERROR:", str(e))
        return Response({"error": str(e)})


# -------------------------------
# 🗑 DELETE DATASET
# -------------------------------
@api_view(['DELETE'])
def delete_dataset(request, id):
    try:
        dataset = Dataset.objects.get(id=id)
        dataset.delete()
        return Response({"message": "Deleted successfully"})
    except Exception as e:
        return Response({"error": str(e)})


# -------------------------------
# 🤖 AI INSIGHTS (HYBRID WORKING)
# -------------------------------
@api_view(['POST'])
def ai_insights(request):
    data = request.data.get("data", [])

    if not data:
        return Response({"insights": "No data provided"})

    try:
        df = pd.DataFrame(data)

        # 🔥 Keep only numeric columns
        numeric_df = df.select_dtypes(include=['number'])

        if numeric_df.empty:
            return Response({"insights": "No meaningful numeric data found"})

        summary = numeric_df.describe().to_dict()

        # -------------------------------
        # 🤖 TRY GEMINI (SHORT RESPONSE)
        # -------------------------------
        if GEMINI_AVAILABLE:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)

                prompt = f"""
                You are a data analyst.

                Dataset summary:
                {summary}

                Give ONLY 3-4 short key insights.
                No stats, no numbers dump.
                Keep it human-like and meaningful.
                """

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )

                if response.text:
                    return Response({"insights": response.text.strip()})

            except Exception as e:
                print("🔥 GEMINI ERROR:", str(e))

        # -------------------------------
        # 🔥 SMART FALLBACK (SHORT AI STYLE)
        # -------------------------------
        insights = []

        # 👉 Trend detection (top 2 only)
        trends = []
        for col in numeric_df.columns:
            values = numeric_df[col].dropna()
            if len(values) < 2:
                continue

            trend = "increasing" if values.iloc[-1] > values.iloc[0] else "decreasing"
            change = abs(values.iloc[-1] - values.iloc[0])

            trends.append((col, trend, change))

        trends = sorted(trends, key=lambda x: x[2], reverse=True)[:2]

        for col, trend, _ in trends:
            insights.append(f"• {col} shows a {trend} trend")

        # 👉 Strong correlation
        corr = numeric_df.corr()

        if len(corr.columns) >= 2:
            pairs = []
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    c = abs(corr.iloc[i, j])
                    pairs.append((corr.columns[i], corr.columns[j], c))

            top_pair = sorted(pairs, key=lambda x: x[2], reverse=True)[0]

            if top_pair[2] > 0.5:
                insights.append(
                    f"• {top_pair[0]} and {top_pair[1]} are strongly related"
                )

        # 👉 Final summary line
        insights.append("• Dataset shows clear patterns and variation")

        return Response({
            "insights": "\n".join(insights[:4])  # 🔥 max 4 lines only
        })

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return Response({
            "insights": "Analysis failed"
        })