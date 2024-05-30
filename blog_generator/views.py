from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import os
import assemblyai as aai
import google.generativeai as genai
from pytube import YouTube
from .models import BlogPost
from django.conf import settings

# Create your views here.

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except(KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status = 400)
        
        # get yt title
        title = yt_title(yt_link)

        # get transcript
        transcription = get_transcription(yt_link, title)
        if not transcription:
            return JsonResponse({'error': "failed to get value"}, status = 500)
        
        print(transcription)
        
        # use OpenAI to generate the blog
        try:
            blog_content = generate_blog_from_transcription(transcription)
            #blog_content = "In the vast Marvel universe, Solim stands out as a mutant with the extraordinary ability to turn his skin into adamantium, a near-indestructible metal. Captured as a child by a ruthless crime lord who saw potential in his shiny skin, Solim was trained to become a deadly assassin. Describing his power as akin to \"adamantium-enforced chainmail,\" Solim is virtually invulnerable to physical injuries and edged weapons, including Wolverine's claws. However, the mystical Muramasa blades can pierce his otherwise impervious skin. \nBeyond his formidable abilities, Solim is driven by a hedonistic pursuit of self-pleasure, often found indulging in music, wine, and women, with little regard for morality. This complex character, shaped by a tragic past and a desire for immediate gratification, adds a fresh and intriguing layer to the Marvel universe. His story is one of power, vulnerability, and the relentless quest for personal satisfaction, making Solim a captivating figure among Marvel's mutants."
        except Exception as e:
            return JsonResponse({'error':e}, status = 500)
        
        if not blog_content:
            return JsonResponse({'error':"failed to generate blog article"}, status = 500)
        
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=blog_content,
        )
        new_blog_article.save()
        
        return JsonResponse({'content':blog_content})      
    else:
        return JsonResponse({'error': 'Invalid request method'}, status = 405)
    

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link, title):
    if title.replace('#','') in [file[:-4] for file in os.listdir(settings.MEDIA_ROOT)]:
        return settings.MEDIA_ROOT+'\\'+title.replace('#','')+'.mp3'
    else:
        yt = YouTube(link)
        print('start downloading')
        video = yt.streams.filter(only_audio=True).first()
        out_file = video.download(output_path=settings.MEDIA_ROOT)
        base, ext = os.path.splitext(out_file)
        new_file = base+'.mp3'
        os.rename(out_file, new_file)
        return new_file

def get_transcription(link, title): # using assemblyAI API
    audio_file = download_audio(link, title)
    API_KEY = 'edd8142bd945408d8c826b00c577cfe5'
    aai.settings.api_key = API_KEY
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    print('content transcribed')
    return transcript.text

def generate_blog_from_transcription(transcription):
    genai.configure(api_key='AIzaSyCA0KGsJQ9OQ40kqQJgKe2XNgvWbHrj3e0')
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"Based on the following transcript from a Youtube video, write a comprehensive blog article, try avoid bold, italic words, and point, just make it a paragraph: \n\n {transcription} \n\n Article:"
    response = model.generate_content(prompt)
    print('content is generated')
    print(response)
    generated_content = response.text

    return generated_content

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles':blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail':blog_article_detail})
    else:
        return redirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid user"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST': # user trying to sign up
        print(request.POST)
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        print(f"Username: {username}, Email: {email}, Password: {password}")
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except Exception as e:
                error_message = e
                print(e)
                return render(request, 'signup.html', {'error_message': error_message})

        else:
            error_message = 'Password dont match'
            return render(request, 'signup.html', {'error_message': error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')

# 2:10:51
